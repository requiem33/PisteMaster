<template>
  <div class="pool-ranking-container">
    <el-card shadow="never" class="ranking-card">
      <template #header>
        <div class="card-header">
          <div class="left">
            <span>{{ $t('event.pool.stageRanking') }}</span>
            <el-tag type="info" class="ml-10">{{ $t('event.pool.fencerCount', {n: sortedRanking.length}) }}</el-tag>
          </div>
          <div class="right">
            <el-button type="warning" plain icon="Download">{{ $t('event.pool.exportRanking') }}</el-button>
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
        <el-table-column :label="$t('event.pool.stageRankingShort')" width="100" align="center">
          <template #default="scope">
            <span :class="['rank-number', scope.row.pool_rank <= 3 ? 'top-three' : '']">
              {{ scope.row.pool_rank }}
            </span>
          </template>
        </el-table-column>

        <el-table-column :label="$t('event.ranking.name')" min-width="150">
          <template #default="scope">
            <div class="fencer-name">
              <strong>{{ scope.row.last_name }}</strong> {{ scope.row.first_name }}
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="country_code" :label="$t('event.ranking.country')" width="100" align="center"/>

        <el-table-column :label="$t('event.pool.VM')" width="110" align="center">
          <template #default="scope">
            <span v-if="scope.row.is_bye">BYE</span>
            <span v-else>{{ scope.row.v_m !== undefined ? scope.row.v_m.toFixed(3) : 'N/A' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="ind" :label="$t('event.pool.Ind')" width="90" align="center">
          <template #default="{ row }">{{ row.is_bye ? '-' : row.ind }}</template>
        </el-table-column>
        <el-table-column prop="ts" :label="$t('event.pool.TS')" width="90" align="center">
          <template #default="{ row }">{{ row.is_bye ? '-' : row.ts }}</template>
        </el-table-column>
        <el-table-column prop="tr" :label="$t('event.pool.TR')" width="90" align="center">
          <template #default="{ row }">{{ row.is_bye ? '-' : row.tr }}</template>
        </el-table-column>

        <el-table-column :label="$t('event.pool.status')" width="100" align="center">
          <template #default="scope">
            <el-tag v-if="scope.row.is_bye" type="warning" effect="dark">{{ $t('event.pool.byeAdvanced') }}</el-tag>
            <el-tag v-else :type="scope.row.is_qualified ? 'success' : 'danger'" effect="dark">
              {{ scope.row.is_qualified ? $t('event.pool.qualified') : $t('event.pool.eliminated') }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <div class="ranking-footer">
      <div class="legend">
        <span class="legend-item"><i
            class="dot success"></i> {{ $t('event.pool.qualifiedLine', {n: 100 - (stageConfig?.config?.elimination_rate || 20)}) }}%</span>
      </div>
      <el-button type="primary" size="large" @click="proceedToNextStage" :loading="isSaving">
        {{ $t('event.pool.completeStage') }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import {ref, computed, onMounted} from 'vue'
import {useI18n} from 'vue-i18n'
import {DataManager} from '@/services/DataManager'
import {ElMessage} from 'element-plus'

const {t} = useI18n()

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
      ElMessage.error(t('event.pool.stageConfigError'));
      return;
    }

    const [liveFencers, poolResults] = await Promise.all([
      DataManager.getFencersForStage(props.eventId, props.stageIndex),
      DataManager.getEventPoolRanking(props.eventId, stageId)
    ]);
    allFencersForStage.value = liveFencers;
    poolResultsFencers.value = poolResults;

  } catch (_error) {
    ElMessage.error(t('event.pool.loadRankingFailed'));
  } finally {
    loading.value = false
  }
}

const sortedRanking = computed(() => {
  if (allFencersForStage.value.length === 0) {return [];}

  const resultsMap = new Map(poolResultsFencers.value.map(f => [f.id, f]));

  const enrichedList = allFencersForStage.value.map(fencer => {
    const result = resultsMap.get(fencer.id);
    if (result) {
      return {...fencer, ...result, is_bye: false};
    } else {
      const byeCount = props.stageConfig?.config?.byes || 0;
      if (fencer.current_rank <= byeCount) {
        return {...fencer, is_bye: true};
      }
      return {...fencer, v: 0, m: 0, ts: 0, tr: 0, ind: 0, v_m: 0, is_bye: false};
    }
  });

  const sorted = enrichedList.sort((a, b) => {
    if (a.is_bye && !b.is_bye) {return -1;}
    if (!a.is_bye && b.is_bye) {return 1;}
    if (a.is_bye && b.is_bye) {return a.current_rank - b.current_rank;}

    if (b.v_m !== a.v_m) {return b.v_m - a.v_m;}
    if (b.ind !== a.ind) {return b.ind - a.ind;}
    return b.ts - a.ts;
  });

  const eliminationRate = props.stageConfig?.config?.elimination_rate || 20;
  const qualifiedCount = Math.floor(sorted.length * (1 - eliminationRate / 100));

  return sorted.map((fencer, index) => ({
    ...fencer,
    pool_rank: index + 1,
    is_qualified: fencer.is_bye || (index < qualifiedCount)
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
    ElMessage.success(t('event.pool.stageRankingSaved'));
    emit('next');

  } catch (error) {
    console.error("保存阶段排名失败:", error);
    ElMessage.error(t('common.messages.operationFailed'));
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
