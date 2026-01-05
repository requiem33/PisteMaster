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
            placeholder="操作指南：&#10;1. 在 Excel 中选中数据列（姓、名、性别、国家、排名）并复制。&#10;2. 在此处粘贴。&#10;3. 点击下方解析按钮。"
        />
        <div class="paste-actions">
          <el-button type="primary" @click="parsePasteData">开始解析并导入表格</el-button>
          <span class="hint">解析器支持 Tab 分隔符（Excel默认）和空格分隔。</span>
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
/* 路径：src/components/tournament/FencerImport.vue */
import {onMounted, ref} from 'vue'
import {ElMessage, ElMessageBox} from 'element-plus'
import {DataManager} from '@/services/DataManager'
import {v4 as uuidv4} from 'uuid'

const props = defineProps<{
  eventId: string,
  weapon?: string // 可选，用于限制主剑种
}>()

const emit = defineEmits(['imported'])

interface FencerRow {
  last_name: string
  first_name: string
  gender: string
  country_code: string
  current_ranking: number | null
}

const fencers = ref<FencerRow[]>([])
const showPasteArea = ref(false)
const rawPasteData = ref('')
const isSubmitting = ref(false)
const loading = ref(false)

const addRow = () => {
  fencers.value.push({
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

const parsePasteData = () => {
  if (!rawPasteData.value.trim()) return

  const rows = rawPasteData.value.trim().split('\n')
  let addedCount = 0

  rows.forEach(row => {
    // 匹配制表符(Excel复制)或多个空格
    const cols = row.split(/[\t]+| {2,}/)
    if (cols.length >= 2) {
      fencers.value.push({
        last_name: cols[0]?.trim() || '',
        first_name: cols[1]?.trim() || '',
        gender: cols[2]?.trim().toUpperCase().startsWith('F') ? 'F' : 'M',
        country_code: cols[3]?.trim().toUpperCase() || 'CHN',
        current_ranking: parseInt(cols[4]) || 999
      })
      addedCount++
    }
  })

  ElMessage.success(`成功解析 ${addedCount} 位选手`)
  rawPasteData.value = ''
  showPasteArea.value = false
}

const submitImport = async () => {
  if (fencers.value.length === 0) {
    // 如果允许清空名单，则继续，否则拦截
    const confirmClear = await ElMessageBox.confirm('名单为空，确定要移除该项目所有选手吗？', '提示');
    if (!confirmClear) return;
  }

  isSubmitting.value = true;
  try {
    // 1. 先保存选手基本信息（确保 fencers 表里有这些人）
    const savedFencers = await DataManager.saveFencers(fencers.value);

    // 2. 获取当前表格中所有选手的 ID
    const currentIds = savedFencers.map(f => f.id);

    // 3. 同步关联关系（会自动删除那些被你 removeRow 的人）
    await DataManager.syncEventFencers(props.eventId, currentIds);

    ElMessage.success('名单同步成功');
    emit('imported');
  } catch (error) {
    console.error(error);
    ElMessage.error('保存失败');
  } finally {
    isSubmitting.value = false;
  }
};

const loadExistingFencers = async () => {
  loading.value = true
  try {
    // 从 DataManager 获取已关联到此 eventId 的所有选手详情
    const data = await DataManager.getFencersByEvent(props.eventId)
    fencers.value = data.map(f => ({
      id: f.id, // 保留 ID 极其重要，用于判断是更新还是新增
      last_name: f.last_name,
      first_name: f.first_name,
      gender: f.gender,
      country_code: f.country_code,
      current_ranking: f.current_ranking,
      fencing_id: f.fencing_id // 唯一标识
    }))
  } catch (error) {
    console.error('加载选手失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (props.eventId) {
    loadExistingFencers()
  }
})
</script>

<style scoped lang="scss">
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