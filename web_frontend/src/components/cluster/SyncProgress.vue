<template>
  <div class="sync-progress" v-if="showProgress">
    <el-card shadow="hover" class="sync-card">
      <div class="sync-header">
        <el-icon :class="syncIconClass" :size="18">
          <Loading v-if="isSyncing" />
          <WarningFilled v-else-if="hasOfflineData" />
          <CircleCheck v-else />
        </el-icon>
        <span class="sync-title">{{ syncTitle }}</span>
        <el-button 
          v-if="hasOfflineData && isOnline"
          link 
          type="primary" 
          size="small"
          @click="handleProcessQueue"
          :loading="isProcessing"
        >
          {{ $t('cluster.processQueue') }}
        </el-button>
      </div>

      <el-progress 
        v-if="isSyncing"
        :percentage="syncPercentage"
        :status="syncStatus"
        :stroke-width="4"
        class="sync-progress-bar"
      />

      <div class="sync-details" v-if="showDetails">
        <div class="detail-row" v-if="lastSyncTime">
          <span class="label">{{ $t('cluster.lastSync') }}:</span>
          <span class="value">{{ formatTime(lastSyncTime) }}</span>
        </div>

        <div class="detail-row" v-if="pendingOperations > 0">
          <span class="label">{{ $t('cluster.pendingOps') }}:</span>
          <el-badge :value="pendingOperations" type="warning" />
        </div>

        <div class="detail-row" v-if="conflicts.length > 0">
          <span class="label">{{ $t('cluster.conflicts') }}:</span>
          <el-badge :value="conflicts.length" type="danger" />
          <el-button 
            link 
            type="danger" 
            size="small"
            @click="$emit('showConflicts')"
          >
            {{ $t('cluster.reviewConflicts') }}
          </el-button>
        </div>
      </div>

      <el-collapse v-if="showAdvanced">
        <el-collapse-item :title="$t('cluster.advanced')" name="advanced">
          <div class="advanced-info">
            <div class="info-row">
              <span class="label">{{ $t('cluster.syncId') }}:</span>
              <span class="value monospace">{{ lastSyncId }}</span>
            </div>
            <div class="info-row" v-if="masterUrl">
              <span class="label">{{ $t('cluster.connectedTo') }}:</span>
              <span class="value monospace">{{ masterUrl }}</span>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>

    <Transition name="slide-up">
      <el-alert
        v-if="syncError"
        :title="syncError"
        type="error"
        show-icon
        closable
        @close="clearError"
        class="sync-error"
      />
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Loading, WarningFilled, CircleCheck } from '@element-plus/icons-vue'
import { useSyncStore } from '@/stores/syncStore'

const props = defineProps<{
  showAdvanced?: boolean
  compact?: boolean
}>()

defineEmits<{
  (e: 'showConflicts'): void
}>()

const { t } = useI18n()
const syncStore = useSyncStore()

const isProcessing = ref(false)
let pollInterval: ReturnType<typeof setInterval> | null = null

const isOnline = computed(() => syncStore.isOnline)
const isSyncing = computed(() => syncStore.isLoading)
const pendingOperations = computed(() => syncStore.pendingOperations)
const conflicts = computed(() => syncStore.conflicts)
const lastSyncTime = computed(() => syncStore.lastSyncTime)
const lastSyncId = computed(() => syncStore.lastSyncId)
const masterUrl = computed(() => syncStore.masterUrl)
const syncError = computed(() => syncStore.syncError)

const showProgress = computed(() => {
  if (props.compact) {
    return !isOnline.value || pendingOperations.value > 0 || conflicts.value.length > 0
  }
  return true
})

const showDetails = computed(() => {
  return !props.compact && (lastSyncTime.value || pendingOperations.value > 0 || conflicts.value.length > 0)
})

const hasOfflineData = computed(() => pendingOperations.value > 0)

const syncTitle = computed(() => {
  if (!isOnline.value) {return t('cluster.offlineMode')}
  if (isSyncing.value) {return t('cluster.syncing')}
  if (hasOfflineData.value) {return t('cluster.hasOfflineData')}
  return t('cluster.synced')
})

const syncIconClass = computed(() => {
  if (!isOnline.value) {return 'status-danger'}
  if (isSyncing.value) {return 'status-syncing'}
  if (hasOfflineData.value) {return 'status-warning'}
  return 'status-success'
})

const syncPercentage = ref(0)
const syncStatus = computed(() => {
  if (syncError.value) {return 'exception'}
  return undefined
})

function formatTime(date: Date | null): string {
  if (!date) {return '-'}
  return new Intl.DateTimeFormat(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).format(date)
}

function clearError(): void {
  syncStore.syncError = null
}

async function handleProcessQueue(): Promise<void> {
  isProcessing.value = true
  try {
    await syncStore.processQueue()
    if (pendingOperations.value === 0) {
      ElMessage.success(t('cluster.queueProcessed'))
    }
  } catch (error) {
    console.error('Failed to process queue:', error)
  } finally {
    isProcessing.value = false
  }
}

watch(isSyncing, (syncing) => {
  if (syncing) {
    const interval = setInterval(() => {
      if (syncPercentage.value < 90) {
        syncPercentage.value += 10
      }
    }, 500)
    setTimeout(() => clearInterval(interval), 5000)
  } else {
    syncPercentage.value = 100
    setTimeout(() => {
      syncPercentage.value = 0
    }, 1000)
  }
})

onMounted(() => {
  if (!props.compact) {
    pollInterval = setInterval(() => {
      if (isOnline.value) {
        syncStore.refreshStatus()
        syncStore.loadPendingCount()
      }
    }, 10000)
  }
})

onUnmounted(() => {
  if (pollInterval) {
    clearInterval(pollInterval)
  }
})
</script>

<style scoped lang="scss">
.sync-progress {
  .sync-card {
    .sync-header {
      display: flex;
      align-items: center;
      gap: 8px;

      .sync-title {
        flex: 1;
        font-weight: 500;
      }

      .status-syncing {
        color: var(--el-color-primary);
        animation: spin 1s linear infinite;
      }

      .status-warning {
        color: var(--el-color-warning);
      }

      .status-danger {
        color: var(--el-color-danger);
      }

      .status-success {
        color: var(--el-color-success);
      }
    }

    .sync-progress-bar {
      margin-top: 12px;
    }

    .sync-details {
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid var(--el-border-color-lighter);

      .detail-row {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;

        &:last-child {
          margin-bottom: 0;
        }

        .label {
          color: var(--el-text-color-secondary);
        }
      }
    }

    .advanced-info {
      .info-row {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;

        .label {
          color: var(--el-text-color-secondary);
          min-width: 100px;
        }

        .monospace {
          font-family: monospace;
          font-size: 12px;
        }
      }
    }
  }

  .sync-error {
    margin-top: 12px;
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(-10px);
  opacity: 0;
}
</style>