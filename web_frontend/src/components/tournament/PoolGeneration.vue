<template>
  <div class="pool-gen-container">
    <el-card shadow="never" class="config-section">
      <el-form :inline="true" :model="config">
        <el-form-item label="每组人数">
          <el-select v-model="config.sizePerPool" style="width: 100px">
            <el-option :value="4">4 人</el-option>
            <el-option :value="5">5 人</el-option>
            <el-option :value="6">6 人</el-option>
            <el-option :value="7">7 人</el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="避让原则">
          <el-checkbox v-model="config.avoidClub" disabled>俱乐部避让</el-checkbox>
          <el-checkbox v-model="config.avoidCountry">国家/地区避让</el-checkbox>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="generatePools">重新生成分组</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="pools-grid">
      <el-row :gutter="20">
        <el-col :md="8" :sm="12" v-for="(pool, pIndex) in pools" :key="pIndex">
          <div class="pool-card">
            <div class="pool-header">
              <span class="pool-name">第 {{ pIndex + 1 }} 组 (Pool {{ pIndex + 1 }})</span>
              <el-tag size="small">{{ pool.length }} 人</el-tag>
            </div>

            <div class="pool-body">
              <div
                  v-for="(fencer, fIndex) in pool"
                  :key="fencer.id"
                  class="fencer-item"
              >
                <span class="seed">#{{ fencer.current_ranking || 'N/A' }}</span>
                <span class="name">{{ fencer.last_name }} {{ fencer.first_name }}</span>
                <span class="ioc">{{ fencer.country_code }}</span>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <footer class="footer-actions">
      <el-button @click="$emit('prev')">返回修改名单</el-button>
      <div class="right">
        <el-button type="warning" plain>手动微调 (Drag & Drop)</el-button>
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

const props = defineProps<{ eventId: string }>()
const emit = defineEmits(['next', 'prev'])

const config = ref({
  sizePerPool: 7,
  avoidClub: true,
  avoidCountry: true
})

// 模拟从上一步传入或从 API 获取的已录入选手
const fencers = ref<any[]>([
  {id: 1, last_name: 'ZHANG', first_name: 'San', country_code: 'CHN', current_ranking: 1},
  {id: 2, last_name: 'SMITH', first_name: 'John', country_code: 'USA', current_ranking: 2},
  {id: 3, last_name: 'LEE', first_name: 'Min', country_code: 'KOR', current_ranking: 3},
  {id: 4, last_name: 'WANG', first_name: 'Wu', country_code: 'CHN', current_ranking: 4},
  {id: 5, last_name: 'GARCIA', first_name: 'Maria', country_code: 'ESP', current_ranking: 5},
  {id: 6, last_name: 'MULLER', first_name: 'Hans', country_code: 'GER', current_ranking: 6},
  {id: 7, last_name: 'BROWN', first_name: 'Charlie', country_code: 'USA', current_ranking: 7},
  {id: 8, last_name: 'SATO', first_name: 'Yuki', country_code: 'JPN', current_ranking: 8},
  {id: 9, last_name: 'CHEN', first_name: 'Li', country_code: 'CHN', current_ranking: 9},
  {id: 10, last_name: 'ROSSI', first_name: 'Mario', country_code: 'ITA', current_ranking: 10},
  {id: 11, last_name: 'TANAKA', first_name: 'Ken', country_code: 'JPN', current_ranking: 11},
  {id: 12, last_name: 'DUBOIS', first_name: 'Jean', country_code: 'FRA', current_ranking: 12},
])

const pools = ref<any[][]>([])

/**
 * 核心算法：蛇形分配 (Snake Seeding)
 */
const generatePools = () => {
  // 1. 按排名升序排列
  const sortedFencers = [...fencers.value].sort((a, b) =>
      (a.current_ranking || 999) - (b.current_ranking || 999)
  )

  // 2. 计算需要的小组数量
  const poolCount = Math.ceil(sortedFencers.length / config.value.sizePerPool)
  const result: any[][] = Array.from({length: poolCount}, () => [])

  // 3. 执行蛇形分配
  sortedFencers.forEach((fencer, index) => {
    const round = Math.floor(index / poolCount)
    const isForward = round % 2 === 0

    let poolIndex
    if (isForward) {
      poolIndex = index % poolCount
    } else {
      poolIndex = (poolCount - 1) - (index % poolCount)
    }

    result[poolIndex].push(fencer)
  })

  pools.value = result
  ElMessage.success(`已生成 ${poolCount} 个小组`)
}

const confirmPools = () => {
  // 逻辑：将分组结果保存到 Django 后端
  console.log('最终分组结果:', pools.value)
  emit('next')
}

onMounted(() => {
  generatePools()
})
</script>

<style scoped lang="scss">
.pool-gen-container {
  .config-section {
    margin-bottom: 30px;
    background-color: var(--el-fill-color-light);
  }

  .pools-grid {
    margin-bottom: 40px;
  }

  .pool-card {
    background: #fff;
    border: 1px solid var(--el-border-color-light);
    border-radius: 8px;
    margin-bottom: 20px;
    overflow: hidden;

    .pool-header {
      background: var(--el-color-primary-light-9);
      padding: 10px 15px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--el-border-color-lighter);

      .pool-name {
        font-weight: bold;
        color: var(--el-color-primary);
      }
    }

    .pool-body {
      padding: 10px 0;

      .fencer-item {
        display: flex;
        align-items: center;
        padding: 8px 15px;
        font-size: 13px;
        border-bottom: 1px solid #f9f9f9;

        &:last-child {
          border-bottom: none;
        }

        .seed {
          width: 40px;
          color: #909399;
          font-family: monospace;
        }

        .name {
          flex: 1;
          font-weight: 500;
        }

        .ioc {
          color: var(--el-color-info);
          font-size: 11px;
        }
      }
    }
  }

  .footer-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 20px;
    border-top: 1px solid var(--el-border-color-lighter);
  }
}
</style>