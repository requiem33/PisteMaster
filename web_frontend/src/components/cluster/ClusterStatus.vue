<template>
  <el-card class="cluster-status-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <el-icon :size="20">
          <Monitor />
        </el-icon>
        <span>{{ $t('cluster.title') }}</span>
        <el-tag 
          :type="statusTagType" 
          size="small"
          class="status-tag"
        >
          {{ statusLabel }}
        </el-tag>
        <el-button
          v-if="canAccessSettings"
          size="small"
          text
          @click="router.push('/settings')"
          class="settings-btn"
        >
          <el-icon><Setting /></el-icon>
          {{ $t('cluster.settings') }}
        </el-button>
      </div>
    </template>

    <el-skeleton v-if="isLoading" :rows="3" animated />

    <template v-else>
      <div class="status-section">
        <div class="status-row">
          <span class="label">{{ $t('cluster.mode') }}:</span>
          <el-tag size="small" :type="clusterStatus?.mode === 'cluster' ? 'success' : 'info'">
            {{ clusterStatus?.mode === 'cluster' ? $t('cluster.modeCluster') : $t('cluster.modeSingle') }}
          </el-tag>
        </div>

        <div class="status-row">
          <span class="label">{{ $t('cluster.role') }}:</span>
          <el-tag v-if="clusterStatus?.mode === 'single'" size="small" type="info">
            {{ $t('cluster.modeSingle') }}
          </el-tag>
          <el-tag v-else size="small" :type="clusterStatus?.isMaster ? 'warning' : ''">
            {{ clusterStatus?.isMaster ? $t('cluster.roleMaster') : $t('cluster.roleFollower') }}
          </el-tag>
        </div>

        <div class="status-row">
          <span class="label">{{ $t('cluster.nodeId') }}:</span>
          <span class="value monospace">{{ clusterStatus?.nodeId || '-' }}</span>
        </div>

        <div v-if="clusterStatus?.masterUrl" class="status-row">
          <span class="label">{{ $t('cluster.masterUrl') }}:</span>
          <span class="value monospace">{{ clusterStatus.masterUrl }}</span>
        </div>

        <div class="status-row">
          <span class="label">{{ $t('cluster.syncLag') }}:</span>
          <span class="value">{{ clusterStatus?.syncLag ?? 0 }}</span>
        </div>

        <div class="status-row">
          <span class="label">{{ $t('cluster.networkStatus') }}:</span>
          <el-tag size="small" :type="isOnline ? 'success' : 'danger'">
            {{ isOnline ? $t('cluster.online') : $t('cluster.offline') }}
          </el-tag>
        </div>
      </div>

      <el-divider v-if="clusterStatus?.peers && clusterStatus.peers.length > 0" />

      <div v-if="clusterStatus?.peers && clusterStatus.peers.length > 0" class="peers-section">
        <div class="section-title">{{ $t('cluster.peers') }} ({{ clusterStatus.peers.length }})</div>
        <el-table :data="clusterStatus.peers" size="small" max-height="200">
          <el-table-column prop="nodeId" :label="$t('cluster.nodeId')" min-width="120">
            <template #default="{ row }">
              <span class="monospace">{{ row.nodeId }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="role" :label="$t('cluster.role')" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="row.role === 'master' ? 'warning' : ''">
                {{ row.role === 'master' ? $t('cluster.roleMaster') : $t('cluster.roleFollower') }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="ipAddress" :label="$t('cluster.ipAddress')" width="120">
            <template #default="{ row }">
              <span class="monospace">{{ row.ipAddress || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="isHealthy" :label="$t('cluster.health')" width="80">
            <template #default="{ row }">
              <el-icon :class="row.isHealthy ? 'healthy-icon' : 'unhealthy-icon'">
                <SuccessFilled v-if="row.isHealthy" />
                <CircleClose v-else />
              </el-icon>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <el-divider />

      <div class="actions-section">
        <el-button 
          size="small" 
          @click="handleRefresh"
          :loading="isRefreshing"
        >
          <el-icon><Refresh /></el-icon>
          {{ $t('cluster.refresh') }}
        </el-button>

        <el-button 
          v-if="!isMaster && isOnline"
          size="small" 
          type="primary"
          @click="handleFullSync"
          :loading="isSyncing"
        >
          <el-icon><Connection /></el-icon>
          {{ $t('cluster.fullSync') }}
        </el-button>
      </div>
    </template>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Monitor, Refresh, Connection, SuccessFilled, CircleClose, Setting } from '@element-plus/icons-vue'
import { useSyncStore } from '@/stores/syncStore'
import { useAuthStore } from '@/stores/authStore'
import { isElectron } from '@/utils/platform'
import type { ClusterStatus } from '@/types/cluster'

const router = useRouter()
const { t } = useI18n()
const syncStore = useSyncStore()
const authStore = useAuthStore()

const isLoading = ref(true)
const isRefreshing = ref(false)
const isSyncing = ref(false)

const clusterStatus = ref<ClusterStatus | null>(null)
const isOnline = computed(() => syncStore.isOnline)
const isMaster = computed(() => clusterStatus.value?.isMaster ?? false)

const canAccessSettings = computed(() => {
  if (!isElectron()) {
    return false
  }
  return authStore.isAdmin || authStore.isScheduler
})

const statusTagType = computed(() => {
  if (!isOnline.value) {return 'danger'}
  if (clusterStatus.value?.mode === 'single') {return 'info'}
  if (clusterStatus.value?.isMaster) {return 'warning'}
  return 'success'
})

const statusLabel = computed(() => {
  if (!isOnline.value) {return t('cluster.statusOffline')}
  if (clusterStatus.value?.mode === 'single') {return t('cluster.statusSingle')}
  if (clusterStatus.value?.isMaster) {return t('cluster.statusMaster')}
  return t('cluster.statusFollower')
})

async function loadStatus(): Promise<void> {
  isLoading.value = true
  try {
    await syncStore.refreshStatus()
    clusterStatus.value = syncStore.clusterStatus
  } catch (error) {
    console.error('Failed to load cluster status:', error)
  } finally {
    isLoading.value = false
  }
}

async function handleRefresh(): Promise<void> {
  isRefreshing.value = true
  try {
    await loadStatus()
    ElMessage.success(t('cluster.refreshSuccess'))
  } catch (_error) {
    ElMessage.error(t('cluster.refreshFailed'))
  } finally {
    isRefreshing.value = false
  }
}

async function handleFullSync(): Promise<void> {
  isSyncing.value = true
  try {
    await syncStore.fullSync()
    ElMessage.success(t('cluster.syncSuccess'))
  } catch (_error) {
    ElMessage.error(t('cluster.syncFailed'))
  } finally {
    isSyncing.value = false
  }
}

onMounted(() => {
  loadStatus()
})
</script>

<style scoped lang="scss">
.cluster-status-card {
  .card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .status-tag {
      margin-left: auto;
    }

    .settings-btn {
      margin-left: 8px;
    }
  }

  .status-section {
    .status-row {
      display: flex;
      align-items: center;
      padding: 8px 0;
      border-bottom: 1px solid var(--el-border-color-lighter);

      &:last-child {
        border-bottom: none;
      }

      .label {
        color: var(--el-text-color-secondary);
        min-width: 100px;
      }

      .value {
        color: var(--el-text-color-primary);
        
        &.monospace {
          font-family: monospace;
          font-size: 12px;
        }
      }
    }
  }

  .peers-section {
    .section-title {
      font-weight: 500;
      margin-bottom: 12px;
      color: var(--el-text-color-primary);
    }

    .monospace {
      font-family: monospace;
      font-size: 12px;
    }

    .healthy-icon {
      color: var(--el-color-success);
    }

    .unhealthy-icon {
      color: var(--el-color-danger);
    }
  }

  .actions-section {
    display: flex;
    gap: 12px;
  }
}
</style>