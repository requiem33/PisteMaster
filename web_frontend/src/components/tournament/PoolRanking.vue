<template>
  <div class="pool-ranking-container">
    <el-card shadow="never" class="ranking-card">
      <template #header>
        <div class="card-header">
          <div class="left">
            <span>小组赛总排名 (Overall Ranking)</span>
            <el-tag type="info" class="ml-10">{{ sortedRanking.length }} 名选手</el-tag>
          </div>
          <div class="right">
            <el-button type="warning" plain icon="Download">导出排名表</el-button>
          </div>
        </div>
      </template>

      <!-- 排名表格 -->
      <el-table
          v-loading="loading"
          :data="sortedRanking"
          border
          stripe
          style="width: 100%"
          :row-class-name="getRowClass"
      >
        <el-table-column label="排名" width="70" align="center">
          <template #default="scope">
            <span :class="['rank-number', scope.$index < 3 ? 'top-three' : '']">
              {{ scope.$index + 1 }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="姓名" min-width="150">
          <template #default="scope">
            <div class="fencer-name">
              <strong>{{ scope.row.last_name }}</strong> {{ scope.row.first_name }}
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="country_code" label="国家/地区" width="100" align="center"/>

        <el-table-column label="V/M (胜率)" width="110" align="center">
          <template #default="scope">
            {{ scope.row.v_m.toFixed(3) }}
          </template>
        </el-table-column>

        <el-table-column prop="ind" label="Ind. (净胜)" width="90" align="center"/>
        <el-table-column prop="ts" label="TS (得分)" width="90" align="center"/>
        <th class="col-stat">TR</th> <!-- 对应 prop="tr" -->
        <el-table-column prop="tr" label="TR (失分)" width="90" align="center"/>

        <el-table-column label="状态" width="100" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.is_qualified ? 'success' : 'danger'" effect="dark">
              {{ scope.row.is_qualified ? '晋级' : '淘汰' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <div class="ranking-footer">
      <div class="legend">
        <span class="legend-item"><i class="dot success"></i> 晋级线：前 80%</span>
        <span class="legend-item"><i class="dot danger"></i> 淘汰线：后 20% (或因弃权)</span>
      </div>
      <el-button type="primary" size="large" @click="proceedToDE">
        生成淘汰赛对阵图 (DE)
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import {ref, computed, onMounted} from 'vue'
import {DataManager} from '@/services/DataManager'
import {ElMessage} from 'element-plus'

const props = defineProps<{ eventId: string }>()
const emit = defineEmits(['next'])

const loading = ref(false)
const rawRankingList = ref<any[]>([])

// --- 加载数据 ---
const fetchRankingData = async () => {
  loading.value = true
  try {
    const data = await DataManager.getEventPoolRanking(props.eventId)
    rawRankingList.value = data
  } catch (error) {
    ElMessage.error('无法获取排名数据')
  } finally {
    loading.value = false
  }
}

// --- 核心算法：击剑标准排名排序 ---
const sortedRanking = computed(() => {
  if (rawRankingList.value.length === 0) return []

  // 复制一份数据进行排序
  const list = [...rawRankingList.value]

  return list
      .sort((a, b) => {
        // 1. 比较胜率 (V/M)
        if (b.v_m !== a.v_m) return b.v_m - a.v_m
        // 2. 比较净胜剑 (Ind.)
        if (b.ind !== a.ind) return b.ind - a.ind
        // 3. 比较得分 (TS)
        return b.ts - a.ts
      })
      .map((fencer, index, array) => {
        // 4. 判定晋级状态 (通常规则：小组赛后淘汰 20%~30% 的选手)
        // 这里暂定前 80% 晋级
        const cutoffIndex = Math.ceil(array.length * 0.8)
        return {
          ...fencer,
          is_qualified: index < cutoffIndex
        }
      })
})

const getRowClass = ({row}: any) => {
  return row.is_qualified ? '' : 'eliminated-row'
}

const proceedToDE = () => {
  if (sortedRanking.value.length === 0) {
    ElMessage.warning('暂无排名数据')
    return
  }
  emit('next')
}

onMounted(() => {
  fetchRankingData()
})
</script>

<style scoped lang="scss">
/* 样式保持您的原样，仅做微调 */
.pool-ranking-container {
  padding: 20px;

  .rank-number {
    font-weight: bold;

    &.top-three {
      color: #e6a23c;
      font-size: 1.2em;
    }
  }

  /* 淘汰行样式 */
  :deep(.eliminated-row) {
    background-color: #fef0f0 !important;

    .rank-number, .fencer-name, .cell {
      color: #909399;
      text-decoration: line-through;
    }
  }

  .ranking-footer {
    margin-top: 30px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    background: #fff;
    border: 1px solid #ebeef5;
    border-radius: 8px;

    .legend {
      display: flex;
      gap: 20px;

      .legend-item {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 14px;

        .dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;

          &.success {
            background: #67c23a;
          }

          &.danger {
            background: #f56c6c;
          }
        }
      }
    }
  }
}
</style>
