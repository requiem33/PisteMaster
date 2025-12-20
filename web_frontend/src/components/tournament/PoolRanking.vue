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

      <el-table :data="sortedRanking" border stripe style="width: 100%" :row-class-name="getRowClass">
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
            {{ (scope.row.v_m).toFixed(3) }}
          </template>
        </el-table-column>

        <el-table-column prop="ind" label="Ind. (净胜)" width="90" align="center"/>
        <el-table-column prop="ts" label="TS (得分)" width="90" align="center"/>
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
        <span class="legend-item"><i class="dot danger"></i> 淘汰线：后 20%</span>
      </div>
      <el-button type="primary" size="large" icon="CaretRight" @click="$emit('next')">
        生成淘汰赛对阵图 (DE)
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
/* 路径：src/components/tournament/PoolRanking.vue */
import {computed} from 'vue'

const props = defineProps<{ eventId: string }>()
const emit = defineEmits(['next'])

// 模拟从后端或上一步获取的汇总数据
// 在实际开发中，这些数据应该是 PoolScoring 提交后由后端计算返回的
const mockFencers = [
  {id: 1, last_name: 'CHUMAK', first_name: 'D.', country_code: 'UKR', v: 5, m: 6, ts: 28, tr: 15},
  {id: 2, last_name: 'KANO', first_name: 'K.', country_code: 'JPN', v: 6, m: 6, ts: 30, tr: 10},
  {id: 3, last_name: 'SIKLOSI', first_name: 'G.', country_code: 'HUN', v: 4, m: 6, ts: 24, tr: 18},
  {id: 4, last_name: 'WANG', first_name: 'Z.', country_code: 'CHN', v: 4, m: 6, ts: 24, tr: 20},
  {id: 5, last_name: 'BOREL', first_name: 'Y.', country_code: 'FRA', v: 3, m: 6, ts: 20, tr: 22},
  {id: 6, last_name: 'LIMARDO', first_name: 'R.', country_code: 'VEN', v: 2, m: 6, ts: 18, tr: 25},
  {id: 7, last_name: 'PARK', first_name: 'S.', country_code: 'KOR', v: 1, m: 6, ts: 15, tr: 28},
  {id: 8, last_name: 'MINOBE', first_name: 'K.', country_code: 'JPN', v: 0, m: 6, ts: 10, tr: 30},
]

const sortedRanking = computed(() => {
  return [...mockFencers]
      .map(f => ({
        ...f,
        v_m: f.v / f.m,
        ind: f.ts - f.tr,
        // 这里的逻辑：前 75% 晋级
        is_qualified: true
      }))
      .sort((a, b) => {
        // 1. 比较胜率
        if (b.v_m !== a.v_m) return b.v_m - a.v_m
        // 2. 比较净胜剑
        if (b.ind !== a.ind) return b.ind - a.ind
        // 3. 比较得分
        return b.ts - a.ts
      })
      .map((f, index, arr) => {
        // 标记最后 20% 为淘汰
        const cutoff = Math.floor(arr.length * 0.8)
        return {...f, is_qualified: index < cutoff}
      })
})

const getRowClass = ({row}: any) => {
  return row.is_qualified ? '' : 'eliminated-row'
}
</script>

<style scoped lang="scss">
.pool-ranking-container {
  .ranking-card {
    border-radius: 8px;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: bold;
  }

  .rank-number {
    font-weight: bold;
    font-family: 'Arial';

    &.top-three {
      color: #e6a23c;
      font-size: 1.2em;
    }
  }

  .fencer-name {
    strong {
      color: #303133;
    }
  }

  .ml-10 {
    margin-left: 10px;
  }

  :deep(.eliminated-row) {
    background-color: #fef0f0 !important;
    color: #f56c6c;
    text-decoration: line-through;
    text-decoration-color: rgba(245, 108, 108, 0.4);
  }

  .ranking-footer {
    margin-top: 30px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    border-top: 1px solid #eee;

    .legend {
      display: flex;
      gap: 20px;
      font-size: 14px;

      .legend-item {
        display: flex;
        align-items: center;
        gap: 6px;

        .dot {
          width: 10px;
          height: 10px;
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