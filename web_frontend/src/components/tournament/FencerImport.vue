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
import {ref} from 'vue'
import {ElMessage, ElMessageBox} from 'element-plus'
import {Plus, Memo, Delete, Check} from '@element-plus/icons-vue'

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
  if (fencers.length === 0) return ElMessage.warning('请先添加选手')

  isSubmitting.value = true
  // 这里将对接你的 Django 后端 API
  setTimeout(() => {
    isSubmitting.value = false
    ElMessage.success('选手名单上传成功！')
    // TODO: 调用父组件方法切换到下一步
  }, 1000)
}
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