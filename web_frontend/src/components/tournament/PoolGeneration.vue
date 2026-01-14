<template>
  <div class="pool-gen-container">
    <!-- 1. 顶部配置与统计 -->
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
            {{ byeFencers.length }} 名选手根据规则已轮空 (Byes)
          </el-tag>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 2. 轮空选手展示区 (新增) -->
    <el-collapse v-if="byeFencers.length > 0" class="bye-section">
      <el-collapse-item title="查看已轮空选手 (直接晋级下一轮)" name="1">
        <div class="bye-list">
          <el-tag v-for="f in byeFencers" :key="f.id" class="bye-fencer">
            #{{ f.current_ranking }} {{ f.last_name }} {{ f.first_name }}
          </el-tag>
        </div>
      </el-collapse-item>
    </el-collapse>

    <!-- 3. 小组展示区 -->
    <div class="pools-grid">
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
                @end="handleDragEnd"
            >
              <template #item="{ element }">
                <div class="fencer-item draggable-cursor">
                  <span class="seed">#{{ element.current_ranking }}</span>
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
        <el-text type="info" class="mr-20">手动调整后将自动锁定当前布局</el-text>
        <el-button type="success" size="large" @click="confirmPools">
          确认分组并生成计分表
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

// 【关键修改】接收 stageConfig
const props = defineProps<{
  eventId: string,
  stageConfig: any // 包含 type, config { byes, hits, elimination_rate }
}>()

const emit = defineEmits(['next', 'prev'])

const config = ref({
  sizePerPool: 7, // 默认建议值
  avoidCountry: true
})

const fencers = ref<any[]>([]) // 原始名单
const pools = ref<any[][]>([]) // 分组后的嵌套数组
const loading = ref(false)

// 【新增】计算哪些选手应该轮空
const byeFencers = computed(() => {
  const byeCount = props.stageConfig?.config?.byes || 0;
  return fencers.value.slice(0, byeCount);
});

// 【新增】计算哪些选手需要参加小组赛
const activePoolFencers = computed(() => {
  const byeCount = props.stageConfig?.config?.byes || 0;
  return fencers.value.slice(byeCount);
});

const loadFencers = async () => {
  loading.value = true
  try {
    // 1. 获取名单
    const data = await DataManager.getFencersByEvent(props.eventId)
    fencers.value = data.sort((a, b) => (a.current_ranking || 999) - (b.current_ranking || 999))

    // 2. 尝试从数据库恢复已存分组
    const savedPools = await DataManager.getPoolsDetailed(props.eventId);
    if (savedPools && savedPools.length > 0) {
      pools.value = savedPools;
    } else {
      // 3. 首次进入，自动生成
      generatePools()
    }
  } catch (error) {
    ElMessage.error('无法读取选手名单')
  } finally {
    loading.value = false
  }
}

// 【关键修改】蛇形分组算法，排除轮空选手
const generatePools = () => {
  const source = activePoolFencers.value;
  if (source.length === 0) return

  // 计算组数
  const poolCount = Math.ceil(source.length / config.value.sizePerPool)
  const result: any[][] = Array.from({length: poolCount}, () => [])

  // 蛇形排列
  source.forEach((fencer, index) => {
    const round = Math.floor(index / poolCount)
    const isEvenRound = round % 2 === 0
    let poolIndex = isEvenRound ? (index % poolCount) : (poolCount - 1) - (index % poolCount)
    result[poolIndex].push(fencer)
  })

  pools.value = result
}

const handleReGenerate = () => {
  ElMessageBox.confirm('重新生成将覆盖手动调整的结果，确定吗？', '提示', {type: 'warning'})
      .then(() => generatePools())
}

const handleDragEnd = () => {
  ElMessage({message: '布局已更新', type: 'info', duration: 1000})
}

const confirmPools = async () => {
  try {
    // 保存分组
    await DataManager.savePools(props.eventId, pools.value);
    ElMessage.success('分组已成功保存');
    emit('next');
  } catch (error) {
    ElMessage.error('保存失败');
  }
}

onMounted(() => loadFencers())
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
    background: #fffbe6;
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