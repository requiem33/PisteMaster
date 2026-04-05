<template>
  <div class="settings-page-wrapper">
    <AppHeader />

    <div class="settings-container">
      <el-card class="settings-card">
        <template #header>
          <div class="card-header">
            <h2>{{ $t('cluster.settings') }}</h2>
            <el-tag v-if="!canEdit" type="warning" size="small">
              {{ $t('cluster.permissionDenied') }}
            </el-tag>
          </div>
        </template>

        <el-skeleton v-if="isLoading" :rows="5" animated />

        <template v-else>
          <div class="section">
            <h3>{{ $t('cluster.clusterSettings') }}</h3>

            <div class="mode-switch">
              <span class="label">{{ $t('cluster.mode') }}:</span>
              <el-radio-group
                v-model="localConfig.mode"
                :disabled="!canEdit || isSaving"
                @change="handleModeChange"
              >
                <el-radio-button value="single">
                  {{ $t('cluster.modeSingle') }}
                </el-radio-button>
                <el-radio-button value="cluster">
                  {{ $t('cluster.modeCluster') }}
                </el-radio-button>
              </el-radio-group>
            </div>

            <div class="mode-desc">
              <el-text v-if="localConfig.mode === 'single'" type="info">
                {{ $t('cluster.standaloneMode') }}
              </el-text>
              <el-text v-else type="info">
                {{ $t('cluster.multiNodeMode') }}
              </el-text>
            </div>
          </div>

          <el-divider />

          <div v-if="localConfig.mode === 'cluster'" class="section">
            <h3>{{ $t('cluster.nodeConfiguration') }}</h3>

            <el-form label-width="140px" :disabled="!canEdit || isSaving">
              <el-form-item :label="$t('cluster.nodeId')">
                <div class="node-id-row">
                  <el-input v-model="localConfig.nodeId" disabled class="node-id-input" />
                  <el-button
                    :disabled="!canEdit || isSaving"
                    @click="handleRegenerateNodeId"
                  >
                    {{ $t('cluster.regenerateNodeId') }}
                  </el-button>
                </div>
              </el-form-item>

              <el-form-item :label="$t('cluster.udpPort')">
                <el-input-number
                  v-model="localConfig.udpPort"
                  :min="1024"
                  :max="65535"
                  :disabled="!canEdit || isSaving"
                />
              </el-form-item>

              <el-form-item :label="$t('cluster.apiPort')">
                <el-input-number
                  v-model="localConfig.apiPort"
                  :min="1024"
                  :max="65535"
                  :disabled="!canEdit || isSaving"
                />
              </el-form-item>

              <el-form-item :label="$t('cluster.heartbeat')">
                <el-input-number
                  v-model="localConfig.heartbeatInterval"
                  :min="1"
                  :max="60"
                  :disabled="!canEdit || isSaving"
                />
                <span class="unit"> {{ $t('cluster.seconds') }}</span>
              </el-form-item>

              <el-form-item :label="$t('cluster.masterIp')">
                <el-input
                  v-model="localConfig.masterIp"
                  :placeholder="$t('cluster.masterIpHint')"
                  :disabled="!canEdit || isSaving"
                  clearable
                />
              </el-form-item>
            </el-form>
          </div>

          <el-divider />

          <div class="section status-section">
            <h3>{{ $t('cluster.currentStatus') }}</h3>

            <div class="status-grid">
              <div class="status-item">
                <span class="label">{{ $t('cluster.mode') }}:</span>
                <el-tag :type="clusterStatus?.mode === 'cluster' ? 'success' : 'info'">
                  {{ clusterStatus?.mode === 'cluster' ? $t('cluster.modeCluster') : $t('cluster.modeSingle') }}
                </el-tag>
              </div>

              <div class="status-item">
                <span class="label">{{ $t('cluster.role') }}:</span>
                <el-tag v-if="clusterStatus?.mode === 'single'" type="info">
                  {{ $t('cluster.modeSingle') }}
                </el-tag>
                <el-tag v-else :type="clusterStatus?.isMaster ? 'warning' : ''">
                  {{ clusterStatus?.isMaster ? $t('cluster.roleMaster') : $t('cluster.roleFollower') }}
                </el-tag>
              </div>

              <div class="status-item">
                <span class="label">{{ $t('cluster.peers') }}:</span>
                <span class="value">{{ clusterStatus?.peers?.length || 0 }}</span>
              </div>

              <div class="status-item">
                <span class="label">{{ $t('cluster.syncLag') }}:</span>
                <span class="value">{{ clusterStatus?.syncLag ?? 0 }}</span>
              </div>

              <div class="status-item">
                <span class="label">{{ $t('cluster.networkStatus') }}:</span>
                <el-tag :type="isOnline ? 'success' : 'danger'">
                  {{ isOnline ? $t('cluster.online') : $t('cluster.offline') }}
                </el-tag>
              </div>
            </div>
          </div>

          <el-divider />

          <div class="actions">
            <el-button :disabled="!canEdit || isSaving" @click="handleReset">
              {{ $t('cluster.resetToDefaults') }}
            </el-button>
            <el-button
              type="primary"
              :loading="isSaving"
              :disabled="!canEdit || !hasChanges"
              @click="handleSave"
            >
              {{ $t('cluster.saveChanges') }}
            </el-button>
          </div>
        </template>
      </el-card>
    </div>

    <el-dialog
      v-model="showConfirmDialog"
      :title="$t('cluster.switchConfirmTitle')"
      width="400px"
    >
      <p>{{ $t('cluster.switchConfirmMessage') }}</p>
      <template #footer>
        <el-button @click="cancelModeChange">{{ $t('cluster.cancel') }}</el-button>
        <el-button type="primary" @click="confirmModeChange">
          {{ $t('cluster.confirm') }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showResetDialog"
      :title="$t('cluster.resetConfirmTitle')"
      width="400px"
    >
      <p>{{ $t('cluster.resetConfirmMessage') }}</p>
      <template #footer>
        <el-button @click="showResetDialog = false">{{ $t('cluster.cancel') }}</el-button>
        <el-button type="danger" @click="confirmReset">
          {{ $t('cluster.confirm') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import AppHeader from '@/components/layout/AppHeader.vue'
import { useAuthStore } from '@/stores/authStore'
import { useSyncStore } from '@/stores/syncStore'
import { ClusterService, type ClusterConfig } from '@/services/cluster/ClusterService'
import { isElectron } from '@/utils/platform'

const { t } = useI18n()
const authStore = useAuthStore()
const syncStore = useSyncStore()

const isLoading = ref(true)
const isSaving = ref(false)
const showConfirmDialog = ref(false)
const showResetDialog = ref(false)
const pendingModeChange = ref<'single' | 'cluster' | null>(null)

const localConfig = ref<ClusterConfig>({
  mode: 'single',
  nodeId: '',
  udpPort: 9000,
  apiPort: 8000,
  heartbeatInterval: 5,
  heartbeatTimeout: 15,
  syncInterval: 3,
  replicaAckRequired: 1,
  ackTimeout: 5000,
  masterIp: null,
})

const originalConfig = ref<ClusterConfig | null>(null)
const clusterStatus = computed(() => syncStore.clusterStatus)
const isOnline = computed(() => syncStore.isOnline)

const canEdit = computed(() => {
  if (!isElectron()) {
    return false
  }
  return authStore.isAdmin || authStore.isScheduler
})

const hasChanges = computed(() => {
  if (!originalConfig.value) {
    return false
  }
  return JSON.stringify(localConfig.value) !== JSON.stringify(originalConfig.value)
})

async function loadConfig(): Promise<void> {
  isLoading.value = true
  try {
    const config = await ClusterService.getConfig()
    if (config) {
      localConfig.value = { ...config }
      originalConfig.value = { ...config }
    }
    await syncStore.refreshStatus()
  } catch (error) {
    console.error('Failed to load config:', error)
    ElMessage.error(t('cluster.loadConfigFailed'))
  } finally {
    isLoading.value = false
  }
}

function handleModeChange(newMode: 'single' | 'cluster'): void {
  if (newMode === originalConfig.value?.mode) {
    pendingModeChange.value = null
    return
  }
  pendingModeChange.value = newMode
  showConfirmDialog.value = true
}

function cancelModeChange(): void {
  showConfirmDialog.value = false
  if (pendingModeChange.value && originalConfig.value) {
    localConfig.value.mode = originalConfig.value.mode
  }
  pendingModeChange.value = null
}

async function confirmModeChange(): Promise<void> {
  showConfirmDialog.value = false
  pendingModeChange.value = null
}

async function handleRegenerateNodeId(): Promise<void> {
  try {
    const newNodeId = await ClusterService.regenerateNodeId()
    if (newNodeId) {
      localConfig.value.nodeId = newNodeId
      ElMessage.success(t('cluster.nodeIdRegenerated'))
    }
  } catch (error) {
    console.error('Failed to regenerate node ID:', error)
    ElMessage.error(t('cluster.regenerateFailed'))
  }
}

function handleReset(): void {
  showResetDialog.value = true
}

async function confirmReset(): Promise<void> {
  showResetDialog.value = false
  isSaving.value = true
  try {
    const config = await ClusterService.resetConfig()
    if (config) {
      localConfig.value = { ...config }
      originalConfig.value = { ...config }
      await syncStore.refreshStatus()
      ElMessage.success(t('cluster.settingsReset'))
    }
  } catch (error) {
    console.error('Failed to reset config:', error)
    ElMessage.error(t('cluster.resetFailed'))
  } finally {
    isSaving.value = false
  }
}

async function handleSave(): Promise<void> {
  if (!hasChanges.value) {
    return
  }

  isSaving.value = true
  try {
    const config = await ClusterService.updateConfig({
      mode: localConfig.value.mode,
      nodeId: localConfig.value.nodeId,
      udpPort: localConfig.value.udpPort,
      apiPort: localConfig.value.apiPort,
      heartbeatInterval: localConfig.value.heartbeatInterval,
      masterIp: localConfig.value.masterIp,
    })

    if (config) {
      localConfig.value = { ...config }
      originalConfig.value = { ...config }
      await syncStore.refreshStatus()
      ElMessage.success(t('cluster.settingsSaved'))
    }
  } catch (error) {
    console.error('Failed to save config:', error)
    ElMessage.error(t('cluster.settingsSaveFailed'))
  } finally {
    isSaving.value = false
  }
}

onMounted(() => {
  if (!canEdit.value) {
    ElMessage.warning(t('cluster.permissionDenied'))
  }
  loadConfig()
})
</script>

<style scoped lang="scss">
.settings-page-wrapper {
  min-height: 100vh;
  background-color: var(--el-bg-color-page);
}

.settings-container {
  max-width: 800px;
  margin: 40px auto;
  padding: 0 20px;
}

.settings-card {
  border-radius: 16px;

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;

    h2 {
      margin: 0;
      font-size: 1.5rem;
    }
  }
}

.section {
  margin-bottom: 24px;

  h3 {
    margin-bottom: 16px;
    color: var(--el-text-color-primary);
  }
}

.mode-switch {
  display: flex;
  align-items: center;
  gap: 16px;

  .label {
    font-weight: 500;
    min-width: 80px;
  }
}

.mode-desc {
  margin-top: 8px;
}

.node-id-row {
  display: flex;
  gap: 12px;

  .node-id-input {
    flex: 1;
  }
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;

  .label {
    color: var(--el-text-color-secondary);
    min-width: 80px;
  }

  .value {
    font-family: monospace;
  }
}

.unit {
  margin-left: 8px;
  color: var(--el-text-color-secondary);
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>