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
          <el-button type="primary" size="small" @click="generatePools">重新按算法生成</el-button>
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
import {ElMessage} from 'element-plus'
import {Rank} from '@element-plus/icons-vue'
import draggable from 'vuedraggable' // 👈 引入拖拽库

const props = defineProps<{ eventId: string }>()
const emit = defineEmits(['next', 'prev'])

const config = ref({
  sizePerPool: 7,
  avoidCountry: true
})

// 初始选手数据（模拟）
const initialFencers = [
  {id: 1, last_name: 'ZHANG', first_name: 'San', country_code: 'CHN', current_ranking: 1},
  {id: 2, last_name: 'SMITH', first_name: 'John', country_code: 'USA', current_ranking: 2},
  {id: 3, last_name: 'LEE', first_name: 'Min', country_code: 'KOR', current_ranking: 3},
  {id: 4, last_name: 'WANG', first_name: 'Wu', country_code: 'CHN', current_ranking: 4},
  {id: 5, last_name: 'GARCIA', first_name: 'Maria', country_code: 'ESP', current_ranking: 5},
  {id: 6, last_name: 'MULLER', first_name: 'Hans', country_code: 'GER', current_ranking: 6},
  {id: 7, last_name: 'BROWN', first_name: 'Charlie', country_code: 'USA', current_ranking: 7},
  {id: 8, last_name: 'SATO', first_name: 'Yuki', country_code: 'JPN', current_ranking: 8},
  {id: 9, last_name: 'CHEN', first_name: 'Li', country_code: 'CHN', current_ranking: 9},
]

const pools = ref<any[][]>([])

// 蛇形算法（与之前一致）
const generatePools = () => {
  const sorted = [...initialFencers].sort((a, b) => a.current_ranking - b.current_ranking)
  const poolCount = Math.ceil(sorted.length / config.value.sizePerPool)
  const result: any[][] = Array.from({length: poolCount}, () => [])

  sorted.forEach((fencer, index) => {
    const round = Math.floor(index / poolCount)
    const poolIndex = (round % 2 === 0) ? (index % poolCount) : (poolCount - 1 - (index % poolCount))
    result[poolIndex].push(fencer)
  })
  pools.value = result
}

const handleDragEnd = () => {
  ElMessage({message: '分组已手动更新', type: 'info', duration: 1000})
}

const confirmPools = () => {
  console.log('保存最终分组到后端:', pools.value)
  emit('next')
}

onMounted(() => {
  generatePools()
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