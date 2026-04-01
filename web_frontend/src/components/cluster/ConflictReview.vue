<template>
  <el-card class="conflict-review-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <div class="header-left">
          <el-icon :size="20" class="warning-icon">
            <WarningFilled />
          </el-icon>
          <span>{{ $t('cluster.conflictReview') }}</span>
        </div>
        <el-badge :value="conflicts.length" type="danger" v-if="conflicts.length > 0" />
      </div>
    </template>

    <el-empty v-if="conflicts.length === 0" :description="$t('cluster.noConflicts')" />

    <template v-else>
      <div class="conflict-stats">
        <el-tag type="danger"> {{ conflicts.length }} {{ $t('cluster.pendingConflicts') }}</el-tag>
      </div>

      <el-table :data="conflicts" style="width: 100%" max-height="400">
        <el-table-column prop="table" :label="$t('cluster.table')" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ row.table }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="recordId" :label="$t('cluster.recordId')" min-width="150">
          <template #default="{ row }">
            <span class="monospace">{{ row.recordId }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="conflictType" :label="$t('cluster.type')" width="140">
          <template #default="{ row }">
            <el-tag :type="getConflictTypeTag(row.conflictType)" size="small">
              {{ getConflictTypeLabel(row.conflictType) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column :label="$t('cluster.versions')" width="100">
          <template #default="{ row }">
            <div class="version-comparison">
              <span class="local-version">L: {{ row.localVersion }}</span>
              <span class="remote-version">R: {{ row.remoteVersion }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column :label="$t('cluster.actions')" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link @click="showConflictDetail(row)">
              <el-icon><View /></el-icon>
            </el-button>
            <el-button-group>
              <el-button 
                size="small" 
                type="success"
                @click="handleResolve(row.id, 'local')"
                :loading="row.isResolving === 'local'"
              >
                {{ $t('cluster.keepLocal') }}
              </el-button>
              <el-button 
                size="small" 
                type="primary"
                @click="handleResolve(row.id, 'remote')"
                :loading="row.isResolving === 'remote'"
              >
                {{ $t('cluster.keepRemote') }}
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>

      <el-divider />

      <div class="bulk-actions">
        <el-button 
          size="small" 
          type="success"
          @click="handleResolveAll('local')"
          :loading="isResolvingAll"
          :disabled="conflicts.length === 0"
        >
          {{ $t('cluster.keepAllLocal') }}
        </el-button>
        <el-button 
          size="small" 
          type="primary"
          @click="handleResolveAll('remote')"
          :loading="isResolvingAll"
          :disabled="conflicts.length === 0"
        >
          {{ $t('cluster.keepAllRemote') }}
        </el-button>
        <el-button 
          size="small"
          @click="handleRefresh"
          :loading="isRefreshing"
        >
          {{ $t('cluster.refresh') }}
        </el-button>
      </div>
    </template>
  </el-card>

  <el-dialog
    v-model="showDetailDialog"
    :title="$t('cluster.conflictDetail')"
    width="600px"
    destroy-on-close
  >
    <el-descriptions :column="1" border>
      <el-descriptions-item :label="$t('cluster.table')">
        <el-tag>{{ selectedConflict?.table }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item :label="$t('cluster.recordId')">
        <span class="monospace">{{ selectedConflict?.recordId }}</span>
      </el-descriptions-item>
      <el-descriptions-item :label="$t('cluster.conflictType')">
        <el-tag :type="getConflictTypeTag(selectedConflict?.conflictType)">
          {{ getConflictTypeLabel(selectedConflict?.conflictType) }}
        </el-tag>
      </el-descriptions-item>
    </el-descriptions>

    <el-divider content-position="left">{{ $t('cluster.localData') }}</el-divider>
    <el-scrollbar max-height="150px">
      <pre class="data-preview">{{ formatJson(selectedConflict?.localData) }}</pre>
    </el-scrollbar>

    <el-divider content-position="left">{{ $t('cluster.remoteData') }}</el-divider>
    <el-scrollbar max-height="150px">
      <pre class="data-preview">{{ formatJson(selectedConflict?.remoteData) }}</pre>
    </el-scrollbar>

    <template #footer>
      <el-button @click="showDetailDialog = false">{{ $t('common.actions.cancel') }}</el-button>
      <el-button type="success" @click="handleResolveFromDetail('local')">
        {{ $t('cluster.keepLocal') }}
      </el-button>
      <el-button type="primary" @click="handleResolveFromDetail('remote')">
        {{ $t('cluster.keepRemote') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { WarningFilled, View } from '@element-plus/icons-vue'
import { useSyncStore } from '@/stores/syncStore'
import type { ConflictItem } from '@/types/cluster'

const { t } = useI18n()
const syncStore = useSyncStore()

const isRefreshing = ref(false)
const isResolvingAll = ref(false)
const showDetailDialog = ref(false)
const selectedConflict = ref<ConflictItem | null>(null)

const conflicts = computed(() => {
  return syncStore.conflicts.map(c => ({
    ...c,
    isResolving: null as string | null
  }))
})

function getConflictTypeTag(type: string | undefined): 'danger' | 'warning' | 'info' {
  switch (type) {
    case 'version_mismatch':
      return 'danger'
    case 'deleted_locally':
    case 'deleted_remotely':
      return 'warning'
    default:
      return 'info'
  }
}

function getConflictTypeLabel(type: string | undefined): string {
  switch (type) {
    case 'version_mismatch':
      return t('cluster.conflictVersionMismatch')
    case 'deleted_locally':
      return t('cluster.conflictDeletedLocally')
    case 'deleted_remotely':
      return t('cluster.conflictDeletedRemotely')
    default:
      return type || '-'
  }
}

function formatJson(data: Record<string, unknown> | undefined): string {
  if (!data) {return '{}'}
  return JSON.stringify(data, null, 2)
}

async function handleResolve(conflictId: string, choice: 'local' | 'remote'): Promise<void> {
  try {
    await syncStore.resolveConflict(conflictId, choice)
    ElMessage.success(t('cluster.resolveSuccess'))
  } catch (error) {
    console.error('Failed to resolve conflict:', error)
    ElMessage.error(t('cluster.resolveFailed'))
  }
}

async function handleResolveAll(choice: 'local' | 'remote'): Promise<void> {
  try {
    await ElMessageBox.confirm(
      t('cluster.confirmResolveAll', { choice: choice === 'local' ? t('cluster.local') : t('cluster.remote') }),
      t('cluster.confirmTitle'),
      { type: 'warning' }
    )
    
    isResolvingAll.value = true
    const conflictIds = syncStore.conflicts.map(c => c.id)
    
    for (const id of conflictIds) {
      await syncStore.resolveConflict(id, choice)
    }
    
    ElMessage.success(t('cluster.resolveAllSuccess'))
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to resolve all conflicts:', error)
      ElMessage.error(t('cluster.resolveFailed'))
    }
  } finally {
    isResolvingAll.value = false
  }
}

async function handleRefresh(): Promise<void> {
  isRefreshing.value = true
  try {
    await syncStore.loadConflicts()
    ElMessage.success(t('cluster.refreshSuccess'))
  } catch (error) {
    console.error('Failed to refresh conflicts:', error)
    ElMessage.error(t('cluster.refreshFailed'))
  } finally {
    isRefreshing.value = false
  }
}

function showConflictDetail(conflict: ConflictItem): void {
  selectedConflict.value = conflict
  showDetailDialog.value = true
}

async function handleResolveFromDetail(choice: 'local' | 'remote'): Promise<void> {
  if (!selectedConflict.value) {return}
  
  await handleResolve(selectedConflict.value.id, choice)
  showDetailDialog.value = false
  selectedConflict.value = null
}

onMounted(() => {
  syncStore.loadConflicts()
})
</script>

<style scoped lang="scss">
.conflict-review-card {
  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;

    .header-left {
      display: flex;
      align-items: center;
      gap: 8px;

      .warning-icon {
        color: var(--el-color-danger);
      }
    }
  }

  .conflict-stats {
    margin-bottom: 16px;
  }

  .monospace {
    font-family: monospace;
    font-size: 12px;
  }

  .version-comparison {
    display: flex;
    flex-direction: column;
    font-size: 12px;

    .local-version {
      color: var(--el-color-success);
    }

    .remote-version {
      color: var(--el-color-primary);
    }
  }

  .bulk-actions {
    display: flex;
    gap: 12px;
  }
}

.data-preview {
  font-family: monospace;
  font-size: 12px;
  background-color: var(--el-fill-color-light);
  padding: 12px;
  border-radius: 4px;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>