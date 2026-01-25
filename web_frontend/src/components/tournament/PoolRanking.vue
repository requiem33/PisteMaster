<template>
  <div class="pool-ranking-container">
    <el-card shadow="never" class="ranking-card">
      <template #header>
        <div class="card-header">
          <div class="left">
            <span>本阶段总排名 (Stage Ranking)</span>
            <el-tag type="info" class="ml-10">{{ sortedRanking.length }} 名选手</el-tag>
          </div>
          <div class="right">
            <el-button type="warning" plain icon="Download">导出排名表</el-button>
          </div>
        </div>
      </template>

      <el-table
          v-loading="loading"
          :data="sortedRanking"
          border
          stripe
          style="width: 100%"
          :row-class-name="getRowClass"
      >
        <el-table-column label="本阶段排名" width="100" align="center">
          <template #default="scope">
            <span :class="['rank-number', scope.row.pool_rank <= 3 ? 'top-three' : '']">
              {{ scope.row.pool_rank }}
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
            <!-- 对于轮空选手，显示 'BYE' -->
            <span v-if="scope.row.is_bye">BYE</span>
            <span v-else>{{ scope.row.v_m !== undefined ? scope.row.v_m.toFixed(3) : 'N/A' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="ind" label="Ind. (净胜)" width="90" align="center">
          <template #default="{ row }">{{ row.is_bye ? '-' : row.ind }}</template>
        </el-table-column>
        <el-table-column prop="ts" label="TS (得分)" width="90" align="center">
          <template #default="{ row }">{{ row.is_bye ? '-' : row.ts }}</template>
        </el-table-column>
        <el-table-column prop="tr" label="TR (失分)" width="90" align="center">
          <template #default="{ row }">{{ row.is_bye ? '-' : row.tr }}</template>
        </el-table-column>

        <el-table-column label="状态" width="100" align="center">
          <template #default="scope">
            <el-tag v-if="scope.row.is_bye" type="warning" effect="dark">轮空晋级</el-tag>
            <el-tag v-else :type="scope.row.is_qualified ? 'success' : 'danger'" effect="dark">
              {{ scope.row.is_qualified ? '晋级' : '淘汰' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <div class="ranking-footer">
      <div class="legend">
        <span class="legend-item"><i
            class="dot success"></i> 晋级线：前 {{ 100 - (stageConfig?.config?.elimination_rate || 20) }}%</span>
      </div>
      <el-button type="primary" size="large" @click="proceedToNextStage" :loading="isSaving">
        完成并进入下一阶段
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import {ref, computed, onMounted} from 'vue'
import {DataManager} from '@/services/DataManager'
import {ElMessage} from 'element-plus'

const props = defineProps<{
  eventId: string,
  stageConfig: any,
  stageIndex: number
}>()

const emit = defineEmits(['next'])

const loading = ref(false)
const isSaving = ref(false)
const allFencersForStage = ref<any[]>([])
const poolResultsFencers = ref<any[]>([])

const loadData = async () => {
  loading.value = true
  try {
    const stageId = props.stageConfig?.id;
    if (!stageId) {
      ElMessage.error("阶段配置错误，无法加载排名");
      return;
    }

    // 数据获取逻辑不变
    const [liveFencers, poolResults] = await Promise.all([
      DataManager.getFencersForStage(props.eventId, props.stageIndex),
      DataManager.getEventPoolRanking(stageId)
    ]);
    allFencersForStage.value = liveFencers;
    poolResultsFencers.value = poolResults;

  } catch (error) {
    ElMessage.error('无法获取本阶段排名数据');
  } finally {
    loading.value = false
  }
}

// 【核心改造】: 重写整个 computed 属性，确保数据完整性
const sortedRanking = computed(() => {
  // 1. 如果基础名单为空，则直接返回
  if (allFencersForStage.value.length === 0) return [];

  // 2. 将已有赛果的选手做成一个 Map，方便快速查找
  const resultsMap = new Map(poolResultsFencers.value.map(f => [f.id, f]));

  // 3. 遍历【完整的】初始选手名单，为每个人注入成绩数据
  const enrichedList = allFencersForStage.value.map(fencer => {
    const result = resultsMap.get(fencer.id);
    if (result) {
      // 如果找到了赛果，则合并对象
      return {...fencer, ...result, is_bye: false};
    } else {
      // 如果没找到（轮空或未计分），检查是否为轮空选手
      const byeCount = props.stageConfig?.config?.byes || 0;
      if (fencer.current_rank <= byeCount) {
        return {...fencer, is_bye: true};
      }
      // 否则，是未计分的普通选手，给予默认成绩
      return {...fencer, v: 0, m: 0, ts: 0, tr: 0, ind: 0, v_m: 0, is_bye: false};
    }
  });

  // 4. 排序：轮空选手优先，然后按赛果排序
  const sorted = enrichedList.sort((a, b) => {
    // 轮空选手排在最前面
    if (a.is_bye && !b.is_bye) return -1;
    if (!a.is_bye && b.is_bye) return 1;
    // 如果都是轮空选手，按原始排名排
    if (a.is_bye && b.is_bye) return a.current_rank - b.current_rank;

    // 如果都是比赛选手，按比赛规则排
    if (b.v_m !== a.v_m) return b.v_m - a.v_m;
    if (b.ind !== a.ind) return b.ind - a.ind;
    return b.ts - a.ts;
  });

  // 5. 最终处理：计算最终排名和晋级状态
  const eliminationRate = props.stageConfig?.config?.elimination_rate || 20;
  const qualifiedCount = Math.floor(sorted.length * (1 - eliminationRate / 100));

  return sorted.map((fencer, index) => ({
    ...fencer,
    pool_rank: index + 1, // 赋予最终的阶段排名
    is_qualified: fencer.is_bye || (index < qualifiedCount) // 轮空自动晋级，或排名在晋级线之上
  }));
});

const proceedToNextStage = async () => {
  isSaving.value = true;
  try {
    const stageResults = sortedRanking.value.map(f => ({
      id: f.id,
      rank: f.pool_rank,
      is_eliminated: !f.is_qualified,
    }));

    await DataManager.updateStageRanking(props.eventId, props.stageIndex, stageResults);
    ElMessage.success('本阶段排名已保存，数据快照已更新');
    emit('next');

  } catch (error) {
    console.error("保存阶段排名失败:", error);
    ElMessage.error('操作失败，请重试');
  } finally {
    isSaving.value = false;
  }
}

const getRowClass = ({row}: any) => {
  return row.is_qualified ? '' : 'eliminated-row'
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
/* 样式保持不变 */
.pool-ranking-container {
  padding: 20px;
}

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

.fencer-name strong {
  color: #303133;
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
}

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
</style>
