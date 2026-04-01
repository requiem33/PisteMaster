<template>
  <div class="final-ranking-container">
    <div class="ranking-actions">
      <div class="buttons">
        <el-button type="primary" icon="Download" @click="exportToExcel">{{ $t('event.ranking.exportResults') }} (Excel)</el-button>
        <el-button type="warning" icon="Share" @click="publishResult">{{ $t('event.ranking.exportResults') }}</el-button>
      </div>
    </div>

    <el-card shadow="never" class="table-card">
      <el-table :data="finalResults" border stripe style="width: 100%" v-loading="loading">
        <el-table-column :label="$t('event.ranking.rank')" width="100" align="center">
          <template #default="scope">
            <div :class="['rank-badge', getMedalClass(scope.row.displayRank)]">
              {{ scope.row.displayRank }}
            </div>
          </template>
        </el-table-column>
        <el-table-column :label="$t('event.ranking.name')" min-width="200">
          <template #default="scope">
            <div class="fencer-cell">
              <span class="full-name">{{ scope.row.last_name }} {{ scope.row.first_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="country_code" :label="$t('event.ranking.country')" width="120" align="center"/>
      </el-table>
    </el-card>

    <div class="footer-note">
      * {{ $t('event.ranking.finalRankingNote') || 'Final ranking calculated based on elimination round progress and pool results.' }}
    </div>
  </div>
</template>

<script setup lang="ts">
import {ref, watch, onMounted} from 'vue'
import {useI18n} from 'vue-i18n'
import {ElMessage} from 'element-plus'
import {DataManager} from '@/services/DataManager'
import type {Stage} from '@/types/tournament';

const {t} = useI18n()

const props = defineProps<{
  eventId: string,
  eventInfo: any
}>()

const finalResults = ref<any[]>([])
const loading = ref(false)

const calculateFinalRanking = async (eventData: any) => {
  loading.value = true;
  try {
    const stages: Stage[] = eventData.rules?.stages || [];
    const dehydratedRanking = eventData.live_ranking;

    const liveRanking = await Promise.all(
        dehydratedRanking.map(async (state: any) => {
          const details = await DataManager.getFencerById(state.id);
          return {...details, ...state};
        })
    );

    const lastStage = stages.length > 0 ? stages[stages.length - 1] : null;
    const hasBronzeMedalMatch = lastStage?.type === 'de' && lastStage.config?.final_stage === 'bronze_medal';

    let maxStageIndex = 0;
    liveRanking.forEach((fencer: any) => {
      const stageKeys = Object.keys(fencer.ranks).map(Number);
      const fencerMaxStage = Math.max(...stageKeys, 0);
      if (fencerMaxStage > maxStageIndex) {
        maxStageIndex = fencerMaxStage;
      }
    });
    
    const enrichedFencers = liveRanking.map((fencer: any) => {
      const stageKeys = Object.keys(fencer.ranks).map(Number);
      const computedFinalStageIndex = Math.max(...stageKeys, 0);
      const finalRankInStage = fencer.ranks[computedFinalStageIndex] ?? 999;
      return {...fencer, finalStageIndex: computedFinalStageIndex, finalRankInStage};
    });
    const fencersWithoutFinalRank = enrichedFencers.filter(f => f.finalRankInStage === 999 && f.finalStageIndex === maxStageIndex);
    if (fencersWithoutFinalRank.length > 0) {
      console.warn('Fencers missing final stage rank:', fencersWithoutFinalRank.map(f => ({ id: f.id, name: f.display_name, ranks: f.ranks })));
    }

    enrichedFencers.sort((a: any, b: any) => {
      if (a.finalStageIndex !== b.finalStageIndex) {
        return b.finalStageIndex - a.finalStageIndex;
      }

      for (let i = a.finalStageIndex; i >= 0; i--) {
        const rankA = a.ranks[i] ?? 999;
        const rankB = b.ranks[i] ?? 999;

        if (rankA !== rankB) {
          return rankA - rankB;
        }
      }

      return 0;
    });

    finalResults.value = enrichedFencers.map((fencer, index) => {
      let displayRank = index + 1;
      if (!hasBronzeMedalMatch && index === 3) {
        displayRank = 3;
      }
      return {...fencer, displayRank: displayRank};
    });

  } catch (e) {
    console.error("Error calculating final ranking:", e);
    ElMessage.error(t('common.messages.operationFailed'))
  } finally {
    loading.value = false;
  }
}

const getMedalClass = (rank: number) => {
  if (rank === 1) {return 'gold'}
  if (rank === 2) {return 'silver'}
  if (rank === 3) {return 'bronze'}
  return ''
}

const exportToExcel = () => {
  ElMessage.info(t('common.messages.operationFailed'))
}
const publishResult = () => {
  ElMessage.info(t('common.messages.operationFailed'))
}

watch(() => props.eventInfo, (newEventInfo) => {
  if (newEventInfo && newEventInfo.live_ranking && newEventInfo.live_ranking.length > 0) {
    calculateFinalRanking(newEventInfo);
  }
}, {
  deep: true,
  immediate: true
});

onMounted(async () => {
  if (props.eventId) {
    try {
      loading.value = true;
      const eventData = await DataManager.getEventById(props.eventId);
      if (eventData && eventData.live_ranking && eventData.live_ranking.length > 0) {
        calculateFinalRanking(eventData);
      }
    } catch (error) {
      console.error('Failed to fetch event data for final ranking:', error);
    } finally {
      loading.value = false;
    }
  }
});
</script>

<style scoped lang="scss">
/* 样式保持不变 */
.final-ranking-container {
  padding: 10px;

  .ranking-actions {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 25px;
    gap: 20px;

    .buttons {
      display: flex;
      gap: 10px;
      flex-shrink: 0;
    }
  }

  .rank-badge {
    width: 30px;
    height: 30px;
    line-height: 30px;
    border-radius: 50%;
    margin: 0 auto;
    font-weight: bold;

    &.gold {
      background: #ffd700;
      color: #fff;
      text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
    }

    &.silver {
      background: #c0c0c0;
      color: #fff;
    }

    &.bronze {
      background: #cd7f32;
      color: #fff;
    }
  }

  .fencer-cell {
    display: flex;
    flex-direction: column;

    .full-name {
      font-weight: bold;
      margin-bottom: 4px;
    }

    .club-tag {
      align-self: flex-start;
      font-size: 10px;
    }
  }

  .points {
    color: var(--el-color-primary);
    font-weight: bold;
    font-family: 'Courier New', Courier, monospace;
  }

  .footer-note {
    margin-top: 20px;
    font-size: 12px;
    color: var(--el-text-color-secondary);
    font-style: italic;
  }
}
</style>