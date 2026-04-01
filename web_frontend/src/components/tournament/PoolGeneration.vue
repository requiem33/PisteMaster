<!-- src/components/tournament/PoolGeneration.vue -->
<template>
  <div class="pool-gen-container">
    <el-card shadow="never" class="config-section">
      <el-form :inline="true" :model="config">
        <el-form-item :label="$t('event.pool.groupSize')">
          <el-input-number v-model="config.sizePerPool" :min="2" :max="10" size="small" @change="generatePools"/>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="small" @click="handleReGenerate">{{ $t('event.pool.regenerate') }}</el-button>
        </el-form-item>
        <el-form-item v-if="byeFencers.length > 0">
          <el-tag type="warning" effect="dark">
            {{ $t('event.pool.byeFencers', {n: byeFencers.length}) }}
          </el-tag>
        </el-form-item>
      </el-form>
    </el-card>

    <el-collapse v-if="byeFencers.length > 0" class="bye-section">
      <el-collapse-item :title="$t('event.pool.viewByeFencers', {n: byeFencers.length})" name="1">
        <div class="bye-list">
          <el-tag v-for="f in byeFencers" :key="f.id" class="bye-fencer">
            #{{ f.current_rank }} {{ f.last_name }} {{ f.first_name }}
          </el-tag>
        </div>
      </el-collapse-item>
    </el-collapse>

    <div v-loading="loading" class="pools-grid">
      <el-row :gutter="20">
        <el-col :md="8" :sm="12" v-for="(pool, pIndex) in pools" :key="pIndex">
          <div class="pool-card">
            <div class="pool-header">
              <span class="pool-name">{{ $t('event.pool.group', {n: pIndex + 1}) }}</span>
              <el-tag size="small" type="info">{{ $t('event.pool.fencerCountShort', {n: pool.length}) }}</el-tag>
            </div>
            <draggable
                v-model="pools[pIndex]"
                group="fencers"
                item-key="id"
                class="pool-body-draggable"
                ghost-class="ghost-item"
            >
              <template #item="{ element }">
                <div class="fencer-item draggable-cursor">
                  <span class="seed">#{{ element.current_rank }}</span>
                  <span class="name">{{ element.last_name }} {{ element.first_name }}</span>
                  <span class="ioc">{{ element.country_code }}</span>
                  <el-icon class="drag-handle">
                    <Rank/>
                  </el-icon>
                </div>
              </template>
            </draggable>
          </div>
        </el-col>
      </el-row>
    </div>

    <footer class="footer-actions">
      <el-button @click="$emit('prev')">{{ $t('event.pool.return') }}</el-button>
      <div class="right">
        <el-button type="success" size="large" @click="confirmPools">
          {{ $t('event.pool.confirmPool') }}
        </el-button>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import {ref, onMounted, computed} from 'vue'
import {useI18n} from 'vue-i18n'
import {ElMessage, ElMessageBox} from 'element-plus'
import {Rank} from '@element-plus/icons-vue'
import draggable from 'vuedraggable'
import {DataManager} from '@/services/DataManager'

const {t} = useI18n()

const props = defineProps<{
  eventId: string,
  stageConfig: any
  stageIndex: number
}>()
const emit = defineEmits(['next', 'prev'])

const config = ref({sizePerPool: 7})
const fencers = ref<any[]>([])
const pools = ref<any[][]>([])
const loading = ref(false)

const byeFencers = computed(() => {
  const byeCount = props.stageConfig?.config?.byes || 0;
  return fencers.value.slice(0, byeCount);
});

const activePoolFencers = computed(() => {
  const byeCount = props.stageConfig?.config?.byes || 0;
  return fencers.value.slice(byeCount);
});

const loadDataForCurrentStage = async () => {
  loading.value = true
  try {
    const stageId = props.stageConfig?.id;
    if (!stageId) {
      ElMessage.error(t('event.pool.stageConfigError'));
      return;
    }

    fencers.value = await DataManager.getFencersForStage(props.eventId, props.stageIndex);
    if (fencers.value.length === 0) {
      ElMessage.warning(t('event.pool.noFencersForPool'));
      return;
    }

    const savedPools = await DataManager.getPoolsDetailed(props.eventId, stageId);
    if (savedPools && savedPools.length > 0) {
      pools.value = savedPools;
    } else {
      generatePools()
    }
  } catch (_error) {
    ElMessage.error(t('event.pool.loadPoolFailed'))
  } finally {
    loading.value = false
  }
}

const generatePools = () => {
  const source = activePoolFencers.value;
  if (source.length === 0) {
    pools.value = [];
    return;
  }
  const poolCount = Math.ceil(source.length / config.value.sizePerPool)
  const result: any[][] = Array.from({length: poolCount}, () => [])
  source.forEach((fencer, index) => {
    const round = Math.floor(index / poolCount)
    const poolIndex = round % 2 === 0 ? (index % poolCount) : (poolCount - 1) - (index % poolCount)
    result[poolIndex].push(fencer)
  })
  pools.value = result
}

const handleReGenerate = () => {
  ElMessageBox.confirm(t('event.pool.regenerate'), t('common.actions.confirm'), {type: 'warning'})
      .then(() => generatePools())
}

const confirmPools = async () => {
  try {
    const stageId = props.stageConfig?.id;
    if (!stageId) {
      ElMessage.error(t('event.pool.stageConfigError'));
      return;
    }
    await DataManager.savePools(props.eventId, stageId, pools.value);
    ElMessage.success(t('event.pool.poolSaved'));
    emit('next');
  } catch (_error) {
    ElMessage.error(t('event.pool.saveFailed'));
  }
}

onMounted(() => loadDataForCurrentStage())
</script>

<style scoped lang="scss">
/* 在原有样式基础上增加 */
.bye-section {
  margin-bottom: 20px;

  .bye-list {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    padding: 10px;
    background: var(--el-fill-color-light);
    border-radius: 4px;
  }

  .bye-fencer {
    font-weight: bold;
  }
}

.pool-gen-container {
  .edit-hint {
    margin-left: 15px;
    font-size: 12px;
    color: var(--el-color-warning);
  }

  .pool-body-draggable {
    min-height: 100px; // 确保空组也能拖入
    padding: 10px 0;
  }

  .fencer-item {
    display: flex;
    align-items: center;
    padding: 10px 15px;
    background: var(--el-bg-color);
    border-bottom: 1px solid var(--el-border-color-lighter);
    transition: background 0.2s;

    &.draggable-cursor {
      cursor: grab;
    }

    &:active {
      cursor: grabbing;
    }

    &:hover {
      background: var(--el-fill-color-light);
    }

    .seed {
      width: 35px;
      font-weight: bold;
      color: var(--el-color-primary);
    }

    .name {
      flex: 1;
    }

    .ioc {
      font-size: 12px;
      color: var(--el-text-color-secondary);
      margin-right: 10px;
    }

    .drag-handle {
      color: var(--el-text-color-placeholder);
      opacity: 0;
      transition: 0.2s;
    }

    &:hover .drag-handle {
      opacity: 1;
    }
  }

  .ghost-item {
    opacity: 0.5;
    background: var(--el-color-primary-light-8) !important;
    border: 1px dashed var(--el-color-primary);
  }

  .pool-card {
    border: 1px solid var(--el-border-color-light);
    border-radius: 8px;
    margin-bottom: 20px;
    background: var(--el-bg-color);

    .pool-header {
      padding: 10px 15px;
      background: var(--el-fill-color-lighter);
      display: flex;
      justify-content: space-between;
      border-bottom: 1px solid var(--el-border-color-light);
    }
  }

  .footer-actions {
    margin-top: 30px;
    padding: 20px;
    border-top: 1px solid var(--el-border-color-lighter);
    display: flex;
    justify-content: space-between;
  }

  .mr-20 {
    margin-right: 20px;
  }
}
</style>