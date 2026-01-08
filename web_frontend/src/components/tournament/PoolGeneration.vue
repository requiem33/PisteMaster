<template>
  <div class="pool-gen-container">
    <el-card shadow="never" class="config-section">
      <el-form :inline="true" :model="config">
        <el-form-item label="每组人数">
          <el-input-number v-model="config.sizePerPool" :min="2" :max="10" size="small"/>
        </el-form-item>
        <el-form-item label="避让原则">
          <el-checkbox v-model="config.avoidCountry">国家/地区自动避让</el-checkbox>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="small" @click="handleReGenerate">重新按算法生成</el-button>
          <span class="edit-hint">提示：你可以直接在下方拖动选手进行手动调组</span>
        </el-form-item>
      </el-form>
    </el-card>

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
      <el-button @click="$emit('prev')">返回修改名单</el-button>
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
/* 路径：src/components/tournament/PoolGeneration.vue */
import {ref, onMounted} from 'vue'
import {ElMessage, ElMessageBox} from 'element-plus'
import {Rank} from '@element-plus/icons-vue'
import draggable from 'vuedraggable'
import {DataManager} from '@/services/DataManager' // 👈 引入 DataManager

const props = defineProps<{ eventId: string }>()
const emit = defineEmits(['next', 'prev'])

const config = ref({
  sizePerPool: 7,
  avoidCountry: true
})

const fencers = ref<any[]>([]) // 存储从数据库查出的原始选手列表
const pools = ref<any[][]>([])
const loading = ref(false)

// --- 加载数据 ---
const loadFencers = async () => {
  loading.value = true
  try {
    // 1. 【关键修改】无论有没有分组，都必须先拿到这个项目的所有选手详情
    // 因为 generatePools 算法依赖 fencers.value 作为“原材料”
    const data = await DataManager.getFencersByEvent(props.eventId)

    if (!data || data.length === 0) {
      ElMessage.warning('当前项目暂无参赛选手，请先导入名单')
      return
    }

    // 填充原始选手列表并排序（为蛇形算法做准备）
    fencers.value = data.sort((a, b) => {
      const rA = a.current_ranking || 999
      const rB = b.current_ranking || 999
      return rA - rB
    })

    // 2. 尝试获取该项目【已经保存过】的分组信息
    const savedPools = await DataManager.getPoolsDetailed(props.eventId)

    if (savedPools && savedPools.length > 0) {
      // 如果有历史分组，直接恢复
      pools.value = savedPools

      // 同步“每组人数”配置
      if (savedPools[0]) {
        config.value.sizePerPool = savedPools[0].length
      }
    } else {
      // 3. 只有在没有历史分组的情况下，才自动执行第一次算法生成
      generatePools()
    }
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('无法读取选手或分组信息')
  } finally {
    loading.value = false
  }
}

// --- 蛇形分组算法 (Serpentine System) ---
const generatePools = () => {
  if (fencers.value.length === 0) return

  const sorted = [...fencers.value]
  // 计算需要分多少组
  const poolCount = Math.ceil(sorted.length / config.value.sizePerPool)
  const result: any[][] = Array.from({length: poolCount}, () => [])

  // 蛇形排列：
  // 组1: 1, 12, 13...
  // 组2: 2, 11, 14...
  // 组3: 3, 10, 15...
  sorted.forEach((fencer, index) => {
    const round = Math.floor(index / poolCount)
    const isEvenRound = round % 2 === 0
    let poolIndex: number

    if (isEvenRound) {
      poolIndex = index % poolCount
    } else {
      poolIndex = (poolCount - 1) - (index % poolCount)
    }

    result[poolIndex].push(fencer)
  })

  pools.value = result
}

const handleReGenerate = () => {
  if (pools.value.length > 0) {
    ElMessageBox.confirm(
        '重新生成将清除你当前的手动调整结果，确定要按算法重新分组吗？',
        '确认重新生成',
        {confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'}
    ).then(() => {
      generatePools()
    }).catch(() => {
    })
  } else {
    generatePools()
  }
}

const handleDragEnd = () => {
  ElMessage({message: '分组已手动更新', type: 'info', duration: 1000})
}

const confirmPools = async () => {
  try {
    // 真正持久化到数据库
    await DataManager.savePools(props.eventId, pools.value);
    ElMessage.success('分组已成功保存');
    emit('next'); // 进入计分页面
  } catch (error) {
    ElMessage.error('分组保存失败');
  }
}

onMounted(() => {
  if (props.eventId) {
    loadFencers()
  }
})
</script>

<style scoped lang="scss">
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