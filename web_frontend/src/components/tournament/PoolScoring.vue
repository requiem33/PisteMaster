<template>
  <div class="pool-scoring-wrapper">
    <div v-if="results.length > 0" class="pools-flex-container">
      <div v-for="(pool, pIndex) in poolGroups" :key="pIndex" class="pool-card">
        <div class="pool-header">
          <span class="pool-tag">Pool {{ pIndex + 1 }}</span>
          <span class="pool-info">{{ pool.fencers.length }} 选手</span>
        </div>

        <div class="table-scroll-wrapper">
          <table class="custom-scoring-table">
            <thead>
            <tr>
              <th class="col-index">#</th>
              <th class="col-name">Name</th>
              <th v-for="n in pool.fencers.length" :key="n" class="col-score-head">{{ n }}</th>
              <th class="col-stat">V</th>
              <th class="col-stat">TS</th>
              <th class="col-stat">TR</th>
              <th class="col-stat highlight">Ind</th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="(fencer, rowIndex) in pool.fencers" :key="fencer.id">
              <td class="cell-index">{{ rowIndex + 1 }}</td>
              <td class="cell-name">
                <div class="fencer-text">
                  <span class="last-name">{{ fencer.last_name }}</span>
                  <span class="country">{{ fencer.country_code }}</span>
                </div>
              </td>

              <td
                  v-for="n in pool.fencers.length"
                  :key="n"
                  class="cell-score"
                  :class="{ 'is-diagonal': rowIndex === n - 1 }"
              >
                <input
                    v-if="rowIndex !== n - 1"
                    v-model="results[pIndex][rowIndex][n-1]"
                    class="score-input"
                    maxlength="2"
                    @input="handleScoreChange(pIndex, rowIndex, n-1)"
                />
              </td>

              <td class="cell-stat v-text">{{ stats[pIndex][rowIndex].V }}</td>
              <td class="cell-stat">{{ stats[pIndex][rowIndex].TS }}</td>
              <td class="cell-stat">{{ stats[pIndex][rowIndex].TR }}</td>
              <td class="cell-stat ind-text">{{ stats[pIndex][rowIndex].Ind }}</td>
            </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div v-else class="loading-state">
      <el-skeleton :rows="5" animated />
    </div>

    <footer class="action-footer">
      <el-button @click="$emit('prev')">返回分组</el-button>
      <div class="summary-info">所有分数已实时保存</div>
      <el-button type="success" size="large" @click="submitScores">保存并查看总排名</el-button>
    </footer>
  </div>
</template>

<script setup lang="ts">
/* 路径：src/components/tournament/PoolScoring.vue */
import {ref, reactive, onMounted} from 'vue'
import {ElMessage} from 'element-plus'

const props = defineProps<{ eventId: string }>()
const emit = defineEmits(['next', 'prev'])

// 模拟多小组数据
const poolGroups = ref([
  {
    fencers: [
      {id: '101', last_name: 'CHUMAK', country_code: 'UKR'},
      {id: '102', last_name: 'KANO', country_code: 'JPN'},
      {id: '103', last_name: 'BOREL', country_code: 'FRA'},
      {id: '104', last_name: 'WANG', country_code: 'CHN'},
      {id: '105', last_name: 'MINOBE', country_code: 'JPN'}
    ]
  },
  {
    fencers: [
      {id: '201', last_name: 'SIKLOSI', country_code: 'HUN'},
      {id: '202', last_name: 'REIZLIN', country_code: 'UKR'},
      {id: '203', last_name: 'KOCH', country_code: 'HUN'},
      {id: '204', last_name: 'LAN', country_code: 'CHN'},
      {id: '205', last_name: 'PIZZO', country_code: 'ITA'},
      {id: '206', last_name: 'LIMARDO', country_code: 'VEN'}
    ]
  },
  {
    fencers: [
      {id: '301', last_name: 'HEINZER', country_code: 'SUI'},
      {id: '302', last_name: 'PARK', country_code: 'KOR'},
      {id: '303', last_name: 'FREILICH', country_code: 'ISR'},
      {id: '304', last_name: 'GAROZZO', country_code: 'ITA'},
      {id: '305', last_name: 'SANTOS', country_code: 'BRA'}
    ]
  }
])

const results = reactive<any[]>([])
const stats = reactive<any[]>([])

const initMatrix = () => {
  // 先清空，确保响应式追踪
  results.length = 0
  stats.length = 0

  poolGroups.value.forEach((pool, pIdx) => {
    const size = pool.fencers.length
    results.push(Array.from({ length: size }, () => Array(size).fill('')))
    stats.push(Array.from({ length: size }, () => ({ V: 0, TS: 0, TR: 0, Ind: 0 })))
  })
}

const handleScoreChange = (pIdx: number, row: number, col: number) => {
  let val = results[pIdx][row][col].toUpperCase()
  if (val === '5') val = 'V'
  results[pIdx][row][col] = val
  calculateStats(pIdx)
}

const calculateStats = (pIdx: number) => {
  const size = poolGroups.value[pIdx].fencers.length
  const currentPoolStats = Array.from({length: size}, () => ({V: 0, TS: 0, TR: 0, Ind: 0}))

  for (let i = 0; i < size; i++) {
    for (let j = 0; j < size; j++) {
      if (i === j) continue
      const score = parseScore(results[pIdx][i][j])
      const oppScore = parseScore(results[pIdx][j][i])

      currentPoolStats[i].TS += score
      currentPoolStats[i].TR += oppScore

      if (results[pIdx][i][j] === 'V' || (score > oppScore && results[pIdx][j][i] !== '')) {
        currentPoolStats[i].V += 1
      }
    }
    currentPoolStats[i].Ind = currentPoolStats[i].TS - currentPoolStats[i].TR
  }
  stats[pIdx] = currentPoolStats
}

const parseScore = (s: string) => s === 'V' ? 5 : (parseInt(s) || 0)

const submitScores = () => {
  ElMessage.success('比分已同步')
  emit('next')
}

onMounted(initMatrix)
</script>

<style scoped lang="scss">
.pool-scoring-wrapper {
  padding: 10px;

  .pools-flex-container {
    display: flex;
    flex-wrap: wrap; /* 核心：一行放不下自动换行 */
    gap: 30px;
    justify-content: flex-start;
  }

  .pool-card {
    background: #fff;
    border: 1px solid #dcdfe6;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    overflow: hidden;
    flex: 0 0 auto; /* 不随 flex 增长拉伸 */
  }

  .pool-header {
    background: #409eff;
    color: white;
    padding: 10px 15px;
    display: flex;
    justify-content: space-between;
    align-items: center;

    .pool-tag {
      font-weight: bold;
    }

    .pool-info {
      font-size: 12px;
      opacity: 0.9;
    }
  }

  .custom-scoring-table {
    border-collapse: collapse;
    font-size: 13px;
    table-layout: fixed; /* 锁定宽度 */

    th, td {
      border: 1px solid #ebeef5;
      text-align: center;
      padding: 0;
    }

    /* 宽度控制 */
    .col-index {
      width: 30px;
    }

    .col-name {
      width: 120px;
    }

    .col-score-head {
      width: 45px;
    }

    /* 计分区表头 */
    .col-stat {
      width: 40px;
      background: #f9f9f9;
    }

    .highlight {
      background: #f0f7ff;
      color: #409eff;
    }

    /* 正方形格子： aspect-ratio 确保宽高 1:1 */
    .cell-score {
      width: 45px;
      height: 45px;
      padding: 0;
      background: white;

      &.is-diagonal {
        background: #909399;
      }
    }

    .score-input {
      width: 100%;
      height: 100%;
      border: none;
      text-align: center;
      font-weight: bold;
      font-size: 16px;
      outline: none;

      &:focus {
        background: #ecf5ff;
      }
    }

    .cell-name {
      text-align: left;
      padding-left: 10px;

      .fencer-text {
        display: flex;
        flex-direction: column;

        .last-name {
          font-weight: bold;
          font-size: 12px;
        }

        .country {
          font-size: 10px;
          color: #909399;
        }
      }
    }

    .cell-stat {
      font-weight: 500;
    }

    .v-text {
      color: #67c23a;
      font-weight: bold;
    }

    .ind-text {
      font-weight: bold;
      color: #409eff;
    }
  }

  .action-footer {
    margin-top: 50px;
    padding: 20px;
    border-top: 1px solid #eee;
    display: flex;
    justify-content: space-between;
    align-items: center;

    .summary-info {
      color: #909399;
      font-style: italic;
    }
  }
}
</style>