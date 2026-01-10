<template>
  <div class="fencer-import-container">
    <div class="action-bar">
      <div class="left">
        <el-button type="primary" icon="Plus" @click="addRow">添加单行</el-button>
        <el-button type="success" icon="Memo" @click="showPasteArea = !showPasteArea">
          {{ showPasteArea ? '关闭粘贴窗' : '从 Excel 批量粘贴' }}
        </el-button>
      </div>
      <div class="right">
        <el-button type="danger" plain icon="Delete" @click="clearAll" :disabled="!fencers.length">
          清空全部
        </el-button>
      </div>
    </div>

    <el-collapse-transition>
      <div v-if="showPasteArea" class="paste-area">
        <el-input
            v-model="rawPasteData"
            type="textarea"
            :rows="8"
            placeholder="操作指南：&#10;1. 在 Excel 或网页中选中数据区域（包含表头或不含均可）并复制。&#10;2. 在此处粘贴。&#10;3. 点击下方【开始解析】按钮。"
        />
        <div class="paste-actions">
          <el-button type="primary" @click="parseAndImport" :loading="isParsing">开始解析并导入</el-button>
          <span class="hint">智能解析器会自动识别 姓、名、性别、国家/地区、排名 等信息。</span>
        </div>
      </div>
    </el-collapse-transition>

    <el-table :data="fencers" border stripe class="fencer-table">
      <el-table-column type="index" label="序号" width="60" align="center"/>
      <el-table-column label="姓 (Last Name)">
        <template #default="scope">
          <el-input v-model="scope.row.last_name" placeholder="必填"/>
        </template>
      </el-table-column>
      <el-table-column label="名 (First Name)">
        <template #default="scope">
          <el-input v-model="scope.row.first_name" placeholder="必填"/>
        </template>
      </el-table-column>
      <el-table-column label="性别" width="100">
        <template #default="scope">
          <el-select v-model="scope.row.gender">
            <el-option label="男" value="M"/>
            <el-option label="女" value="F"/>
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="国家 (IOC)" width="120">
        <template #default="scope">
          <el-input v-model="scope.row.country_code" placeholder="如 CHN" maxlength="3"/>
        </template>
      </el-table-column>
      <el-table-column label="初始排名" width="120">
        <template #default="scope">
          <el-input-number v-model="scope.row.current_ranking" :min="0" controls-position="right" style="width: 100%"/>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="70" align="center">
        <template #default="scope">
          <el-button type="danger" icon="Delete" circle @click="removeRow(scope.$index)"/>
        </template>
      </el-table-column>
    </el-table>

    <footer class="import-footer">
      <div class="info">
        已就绪选手: <span class="count">{{ fencers.length }}</span> 名
      </div>
      <el-button type="primary" size="large" icon="Check" :loading="isSubmitting" @click="submitImport">
        保存名单并进入分组
      </el-button>
    </footer>
  </div>
</template>

<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {ElMessage, ElMessageBox} from 'element-plus'
import {DataManager} from '@/services/DataManager'

const props = defineProps<{
  eventId: string
}>()
const emit = defineEmits(['imported'])

interface FencerRow {
  id?: string;
  last_name: string
  first_name: string
  gender: string
  country_code: string
  current_ranking: number | null
  fencing_id?: string;
}

const fencers = ref<FencerRow[]>([])
const showPasteArea = ref(false)
const rawPasteData = ref('')
const isSubmitting = ref(false)
const isParsing = ref(false)

const addRow = () => {
  fencers.value.unshift({ // 新增行放在最上面，方便查看
    last_name: '',
    first_name: '',
    gender: 'M',
    country_code: 'CHN',
    current_ranking: 999
  })
}

const removeRow = (index: number) => {
  fencers.value.splice(index, 1)
}

const clearAll = () => {
  ElMessageBox.confirm('确定清空当前列表所有选手吗？', '确认', {type: 'warning'})
      .then(() => {
        fencers.value = []
      })
}

/**
 * 核心：智能解析粘贴的数据
 */
const parseAndImport = () => {
  if (!rawPasteData.value.trim()) {
    ElMessage.warning('粘贴内容为空');
    return;
  }
  isParsing.value = true;

  try {
    const lines = rawPasteData.value.trim().split('\n');
    const newFencers: FencerRow[] = [];

    lines.forEach(line => {
      if (!line.trim()) return;

      // 智能分割：优先使用 Tab，否则使用两个或更多空格
      const columns = line.split(/\t| {2,}/).map(col => col.trim());

      // 基础数据清洗和提取
      const lastName = columns[0] || '';
      const firstName = columns[1] || '';

      // 性别解析：查找 'F' 或 '女'
      const genderRaw = (columns.find(c => c.toUpperCase() === 'F' || c === '女') || 'M').toUpperCase();
      const gender = genderRaw.startsWith('F') ? 'F' : 'M';

      // 国家代码解析：查找三位大写字母
      const countryCodeRaw = columns.find(c => /^[A-Z]{3}$/.test(c));
      const country_code = countryCodeRaw || 'CHN';

      // 排名解析：查找纯数字
      let ranking: number | null = 999;
      const rankingStr = columns.find(c => /^\d+$/.test(c) && c.length < 4); // 避免匹配到年份等
      if (rankingStr) {
        ranking = parseInt(rankingStr, 10);
      }

      if (lastName && firstName) {
        newFencers.push({
          last_name: lastName,
          first_name: firstName,
          gender: gender,
          country_code: country_code,
          current_ranking: ranking
        });
      }
    });

    if (newFencers.length > 0) {
      // 合并新旧数据（可以选择是覆盖还是追加）
      // 这里采用追加的方式
      fencers.value = [...fencers.value, ...newFencers];
      ElMessage.success(`成功解析并添加了 ${newFencers.length} 位选手`);
      rawPasteData.value = '';
      showPasteArea.value = false;
    } else {
      ElMessage.error('解析失败，请检查数据格式是否正确');
    }

  } catch (error) {
    console.error("解析粘贴数据时出错:", error);
    ElMessage.error('解析时发生意外错误');
  } finally {
    isParsing.value = false;
  }
};


const submitImport = async () => {
  // 校验逻辑
  const invalidFencer = fencers.value.find(f => !f.last_name || !f.first_name);
  if (invalidFencer) {
    ElMessage.error('存在姓或名为空的选手，请填写完整后再保存');
    return;
  }

  isSubmitting.value = true;
  try {
    const savedFencers = await DataManager.saveFencers(fencers.value);
    const currentIds = savedFencers.map(f => f.id);
    await DataManager.syncEventFencers(props.eventId, currentIds);
    ElMessage.success('名单已成功保存！');
    emit('imported');
  } catch (error) {
    console.error(error);
    ElMessage.error('保存失败，请稍后重试');
  } finally {
    isSubmitting.value = false;
  }
};

const loadExistingFencers = async () => {
  // ... (此函数保持不变)
  try {
    const data = await DataManager.getFencersByEvent(props.eventId)
    fencers.value = data.map(f => ({
      id: f.id,
      last_name: f.last_name,
      first_name: f.first_name,
      gender: f.gender || 'M', // 确保有默认值
      country_code: f.country_code || 'CHN',
      current_ranking: f.current_ranking,
      fencing_id: f.fencing_id
    }))
  } catch (error) {
    console.error('加载选手失败:', error)
  }
}

onMounted(() => {
  if (props.eventId) {
    loadExistingFencers()
  }
})
</script>

<style scoped lang="scss">
/* 样式部分保持不变 */
.fencer-import-container {
  padding: 10px;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.paste-area {
  background: var(--el-fill-color-light);
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  border: 1px dashed var(--el-border-color-darker);

  .paste-actions {
    margin-top: 15px;
    display: flex;
    align-items: center;
    gap: 20px;

    .hint {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }
  }
}

.fencer-table {
  margin-top: 20px;

  :deep(.el-input__inner) {
    text-align: left;
  }
}

.import-footer {
  margin-top: 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-top: 1px solid var(--el-border-color-lighter);

  .info {
    font-size: 16px;

    .count {
      font-weight: bold;
      color: var(--el-color-primary);
      font-size: 24px;
      margin: 0 5px;
    }
  }
}
</style>
