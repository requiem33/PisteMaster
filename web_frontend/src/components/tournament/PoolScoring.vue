<template>
  <div class="pool-scoring-wrapper">
    <div v-if="poolGroups.length > 0" class="pools-flex-container">
      <!-- 遍历每个小组 -->
      <div v-for="(pool, pIndex) in poolGroups" :key="pIndex" class="pool-card">

        <!-- 小组头部：包含标题和操作按钮 -->
        <div class="pool-header">
          <div class="pool-title">
            <span class="pool-tag">第 {{ pIndex + 1 }} 组 (Pool {{ pIndex + 1 }})</span>
            <span class="pool-info">{{ pool.fencers.length }} 选手</span>
          </div>
          <div class="pool-actions">
            <el-button
                size="small"
                type="primary"
                :disabled="!isPoolComplete(pIndex) || isLocked[pIndex]"
                @click="handleConfirmPool(pIndex)"
            >确定
            </el-button>
            <el-button
                size="small"
                :disabled="!isLocked[pIndex]"
                @click="handleUnlockPool(pIndex)"
            >重新录入
            </el-button>
          </div>
        </div>

        <!-- 计分表格核心区 -->
        <div class="table-container">
          <table class="custom-scoring-table">
            <thead>
            <tr>
              <th class="col-index">#</th>
              <th class="col-name">选手姓名 (Name)</th>
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
                <div class="name-box">
                  <span class="full-name">{{ fencer.last_name }} {{ fencer.first_name }}</span>
                  <span class="country-tag">{{ fencer.country_code }}</span>
                </div>
              </td>

              <!-- 循环生成得分输入格 -->
              <td
                  v-for="n in pool.fencers.length"
                  :key="n"
                  class="cell-score"
                  :class="{ 'is-diagonal': rowIndex === n - 1, 'is-locked-cell': isLocked[pIndex] }"
              >
                <input
                    v-if="rowIndex !== n - 1"
                    v-model="results[pIndex][rowIndex][n-1]"
                    class="score-input"
                    :class="{ 'disabled-input': isLocked[pIndex] }"
                    maxlength="2"
                    :disabled="isLocked[pIndex]"
                    @input="handleScoreChange(pIndex, rowIndex, n-1)"
                />
              </td>

              <!-- 统计列 -->
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
      <el-skeleton :rows="10" animated/>
    </div>

    <footer class="action-footer">
      <el-button @click="$emit('prev')">返回分组</el-button>
      <div class="summary-info">比分实时同步中...</div>
      <el-button type="success" size="large" @click="submitScores">查看总排名</el-button>
    </footer>
  </div>
</template>

<script setup lang="ts">
/* ... script 逻辑保持不变（包含 handleScoreChange, calculateStats 等） ... */
import {ref, reactive, onMounted} from 'vue'
import {ElMessage} from 'element-plus'
import {DataManager} from '@/services/DataManager'

const props = defineProps<{ eventId: string }>()
const emit = defineEmits(['next', 'prev'])

const poolGroups = ref<any[]>([])
const results = reactive<any[]>([])
const stats = reactive<any[]>([])
const isLocked = ref<boolean[]>([])

const loadPoolData = async () => {
  try {
    const poolsFromDB = await DataManager.getPoolsByEvent(props.eventId);
    const detailedPools = [];
    results.length = 0;
    stats.length = 0;
    isLocked.value = [];

    for (const p of poolsFromDB) {
      const fencerPromises = p.fencer_ids.map(id => DataManager.getFencerById(id));
      const fencerDetails = await Promise.all(fencerPromises);
      const size = fencerDetails.length;

      detailedPools.push({
        id: p.id,
        pool_number: p.pool_number,
        fencers: fencerDetails.filter(f => f !== undefined)
      });

      results.push(p.results || Array.from({length: size}, () => Array(size).fill('')));
      stats.push(p.stats || Array.from({length: size}, () => ({V: 0, TS: 0, TR: 0, Ind: 0})));
      isLocked.value.push(p.is_locked || false);
    }
    poolGroups.value = detailedPools;
  } catch (e) {
    console.error('加载计分表失败', e);
  }
};

const isPoolComplete = (pIdx: number) => {
  const poolResults = results[pIdx];
  if (!poolResults) return false;
  for (let i = 0; i < poolResults.length; i++) {
    for (let j = 0; j < poolResults[i].length; j++) {
      if (i !== j && (poolResults[i][j] === '' || poolResults[i][j] === null)) return false;
    }
  }
  return true;
};

const handleScoreChange = (pIdx: number, row: number, col: number) => {
  let val = results[pIdx][row][col].toUpperCase();
  if (val === '5') val = 'V';
  results[pIdx][row][col] = val;
  calculateStats(pIdx);
  persistPoolData(pIdx);
};

const calculateStats = (pIdx: number) => {
  const size = poolGroups.value[pIdx].fencers.length;
  const currentPoolStats = Array.from({length: size}, () => ({V: 0, TS: 0, TR: 0, Ind: 0}));
  for (let i = 0; i < size; i++) {
    for (let j = 0; j < size; j++) {
      if (i === j) continue;
      const score = parseScore(results[pIdx][i][j]);
      const oppScore = parseScore(results[pIdx][j][i]);
      currentPoolStats[i].TS += score;
      currentPoolStats[i].TR += oppScore;
      if (results[pIdx][i][j] === 'V' || (score > oppScore && results[pIdx][j][i] !== '')) {
        currentPoolStats[i].V += 1;
      }
    }
    currentPoolStats[i].Ind = currentPoolStats[i].TS - currentPoolStats[i].TR;
  }
  stats[pIdx] = currentPoolStats;
};

const parseScore = (s: string) => s === 'V' ? 5 : (parseInt(s) || 0);

const persistPoolData = async (pIdx: number) => {
  const pool = poolGroups.value[pIdx];
  await DataManager.updatePoolResults(pool.id, results[pIdx], stats[pIdx], isLocked.value[pIdx]);
};

const handleConfirmPool = (pIdx: number) => {
  isLocked.value[pIdx] = true;
  persistPoolData(pIdx);
  ElMessage.success(`第 ${pIdx + 1} 组已锁定`);
};

const handleUnlockPool = (pIdx: number) => {
  isLocked.value[pIdx] = false;
  persistPoolData(pIdx);
};

const submitScores = () => {
  if (isLocked.value.some(locked => !locked)) {
    ElMessage.warning('请先锁定所有小组的比分');
    return;
  }
  emit('next');
};

onMounted(() => loadPoolData());
</script>

<style scoped lang="scss">
.pool-scoring-wrapper {
  padding: 20px;
  background-color: #f8f9fa;

  .pools-flex-container {
    display: flex;
    flex-direction: column; // 改为纵向排列，或者用 wrap
    gap: 40px;
  }

  .pool-card {
    background: #fff;
    border: 1px solid #ebeef5;
    border-radius: 8px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    overflow: hidden;
  }

  .pool-header {
    background: #f5f7fa;
    padding: 12px 20px;
    border-bottom: 1px solid #ebeef5;
    display: flex;
    justify-content: space-between;
    align-items: center;

    .pool-tag {
      font-weight: bold;
      font-size: 16px;
      color: #303133;
      margin-right: 15px;
    }

    .pool-info {
      font-size: 13px;
      color: #909399;
    }
  }

  .table-container {
    padding: 20px;
    overflow-x: auto;
  }

  .custom-scoring-table {
    border-collapse: collapse;
    width: auto;
    min-width: 600px;
    border: 2px solid #303133; // 击剑表格通常外框较粗

    th, td {
      border: 1px solid #303133; // 内部实线
      padding: 0;
      text-align: center;
      vertical-align: middle;
    }

    th {
      background: #f5f7fa;
      height: 40px;
      font-size: 13px;
    }

    /* 列宽控制 */
    .col-index {
      width: 40px;
    }

    .col-name {
      width: 200px;
      text-align: left;
      padding-left: 10px;
    }

    .col-score-head {
      width: 50px;
    }

    .col-stat {
      width: 50px;
      background: #fafafa;
      font-weight: bold;
    }

    .highlight {
      background: #eef5fe;
      color: #409eff;
    }

    .cell-index {
      font-weight: bold;
      background: #f5f7fa;
    }

    .name-box {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0 10px;

      .full-name {
        font-weight: bold;
      }

      .country-tag {
        font-size: 11px;
        color: #909399;
        margin-left: 8px;
      }
    }

    .cell-score {
      width: 50px;
      height: 50px;
      position: relative;

      &.is-diagonal {
        background-color: #606266 !important; // 对角线灰色
      }

      &.is-locked-cell {
        background-color: #f5f7fa;
      }
    }

    .score-input {
      width: 100%;
      height: 100%;
      border: none;
      text-align: center;
      font-size: 18px;
      font-weight: bold;
      background: transparent;
      outline: none;

      &:focus {
        background: #ecf5ff;
      }

      &.disabled-input {
        cursor: not-allowed;
        color: #606266;
      }
    }

    .v-text {
      color: #67c23a;
      font-size: 16px;
    }

    .ind-text {
      color: #409eff;
      font-size: 16px;
    }
  }

  .action-footer {
    margin-top: 40px;
    padding: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid #dcdfe6;
  }
}
</style>
