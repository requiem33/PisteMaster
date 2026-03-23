<!-- src/components/tournament/PoolGeneration.vue -->
<template>
  <div class="pool-gen-container">
    <el-card shadow="never" class="config-section">
      <el-form :inline="true" :model="config">
        <el-form-item label="每组人数">
          <el-input-number v-model="config.sizePerPool" :min="2" :max="10" size="small" @change="generatePools"/>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="small" @click="handleReGenerate">重新按算法生成</el-button>
        </el-form-item>
        <el-form-item v-if="byeFencers.length > 0">
          <el-tag type="warning" effect="dark">
            {{ byeFencers.length }} 名选手根据规则已轮空
          </el-tag>
        </el-form-item>
      </el-form>
    </el-card>

    <el-collapse v-if="byeFencers.length > 0" class="bye-section">
      <el-collapse-item :title="`查看已轮空选手 (${byeFencers.length} 名)`" name="1">
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
              <span class="pool-name">第 {{ pIndex + 1 }} 组</span>
              <el-tag size="small" type="info">{{ pool.length }} 人</el-tag>
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
      <el-button @click="$emit('prev')">返回</el-button>
      <div class="right">
        <el-button type="success" size="large" @click="confirmPools">
          确认分组并进入计分
        </el-button>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import {ref, onMounted, computed} from 'vue'
import {ElMessage, ElMessageBox} from 'element-plus'
import {Rank} from '@element-plus/icons-vue'
import draggable from 'vuedraggable'
import {DataManager} from '@/services/DataManager'

const props = defineProps<{
  eventId: string,
  stageConfig: any // 假设它包含一个唯一的ID，如 stageConfig.id
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

/**
 * 【已修复】加载数据时，传入 stageId
 */
const loadDataForCurrentStage = async () => {
  loading.value = true
  try {
    const stageId = props.stageConfig?.id; // 👈 获取当前阶段的唯一 ID
    if (!stageId) {
      ElMessage.error('阶段配置错误，缺少唯一ID');
      return;
    }

    fencers.value = await DataManager.getFencersForStage(props.eventId, props.stageIndex);
    if (fencers.value.length === 0) {
      ElMessage.warning('当前阶段没有可供比赛的选手。');
      return;
    }

    // 1. 【关键】使用 stageId 来获取本阶段的分组
    const savedPools = await DataManager.getPoolsDetailed(props.eventId, stageId);
    if (savedPools && savedPools.length > 0) {
      pools.value = savedPools;
    } else {
      generatePools()
    }
  } catch (error) {
    ElMessage.error('加载本阶段选手名单失败')
  } finally {
    loading.value = false
  }
}

const generatePools = () => {
  const source = activePoolFencers.value;
  if (source.length === 0) {
    pools.value = []; // 如果没有可分组的选手，确保清空
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
  ElMessageBox.confirm('重新生成将覆盖手动调整，确定吗？', '提示', {type: 'warning'})
      .then(() => generatePools())
}

/**
 * 【已修复】保存分组时，传入 stageId
 */
const confirmPools = async () => {
  try {
    const stageId = props.stageConfig?.id; // 👈 获取当前阶段的唯一 ID
    if (!stageId) {
      ElMessage.error('阶段配置错误，缺少唯一ID');
      return;
    }
    // 2. 【关键】使用 stageId 来保存本阶段的分组
    await DataManager.savePools(props.eventId, stageId, pools.value);
    ElMessage.success('本阶段分组已保存');
    emit('next');
  } catch (error) {
    ElMessage.error('保存失败');
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
    color: #E6A23C;
  }

  .pool-body-draggable {
    min-height: 100px; // 确保空组也能拖入
    padding: 10px 0;
  }

  .fencer-item {
    display: flex;
    align-items: center;
    padding: 10px 15px;
    background: #fff;
    border-bottom: 1px solid #f0f0f0;
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
      color: #409eff;
    }

    .name {
      flex: 1;
    }

    .ioc {
      font-size: 12px;
      color: #999;
      margin-right: 10px;
    }

    .drag-handle {
      color: #ccc;
      opacity: 0;
      transition: 0.2s;
    }

    &:hover .drag-handle {
      opacity: 1;
    }
  }

  .ghost-item {
    opacity: 0.5;
    background: #c8ebfb !important;
    border: 1px dashed #409eff;
  }

  .pool-card {
    border: 1px solid var(--el-border-color-light);
    border-radius: 8px;
    margin-bottom: 20px;
    background: #fff;

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
    border-top: 1px solid #eee;
    display: flex;
    justify-content: space-between;
  }

  .mr-20 {
    margin-right: 20px;
  }
}
</style>