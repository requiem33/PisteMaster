<template>
  <div class="final-ranking-container">
    <div class="ranking-actions">
      <div class="buttons">
        <el-button type="primary" icon="Download" @click="exportToExcel">导出成绩单 (Excel)</el-button>
        <el-button type="warning" icon="Share" @click="publishResult">发布成绩至大屏幕</el-button>
      </div>
    </div>

    <el-card shadow="never" class="table-card">
      <el-table :data="finalResults" border stripe style="width: 100%" v-loading="loading">
        <el-table-column label="名次" width="100" align="center">
          <template #default="scope">
            <!-- 【修改】直接使用我们计算好的 displayRank -->
            <div :class="['rank-badge', getMedalClass(scope.row.displayRank)]">
              {{ scope.row.displayRank }}
            </div>
          </template>
        </el-table-column>
        <el-table-column label="选手 (Fencers)" min-width="200">
          <template #default="scope">
            <div class="fencer-cell">
              <span class="full-name">{{ scope.row.last_name }} {{ scope.row.first_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="country_code" label="地区/国籍" width="120" align="center"/>
        <!-- “小组赛表现”和“最后轮次”列已被移除 -->
      </el-table>
    </el-card>

    <div class="footer-note">
      \* 最终排名计算规则：根据淘汰赛被淘汰轮次排序，同轮次淘汰者按照小组赛成绩排序。
    </div>
  </div>
</template>

<script setup lang="ts">
import {ref, watch} from 'vue'
import {ElMessage} from 'element-plus'
import {DataManager} from '@/services/DataManager'
import type {Stage} from '@/types';

// Props 保持不变
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

    // 1. 【注水】(不变)
    const liveRanking = await Promise.all(
        dehydratedRanking.map(async (state: any) => {
          const details = await DataManager.getFencerById(state.id);
          return {...details, ...state};
        })
    );

    // 2. 【读取配置】(不变)
    const lastStage = stages.length > 0 ? stages[stages.length - 1] : null;
    const hasBronzeMedalMatch = lastStage?.type === 'de' && lastStage.config?.final_stage === 'bronze_medal';

    // 3.【“富集”逻辑】(不变)
    const enrichedFencers = liveRanking.map((fencer: any) => {
      const stageKeys = Object.keys(fencer.ranks).map(Number);
      const finalStageIndex = Math.max(...stageKeys, 0);
      const finalRankInStage = fencer.ranks[finalStageIndex] ?? 999;
      return {...fencer, finalStageIndex, finalRankInStage};
    });

    // 4.【核心改造：实现级联比较排序】
    // 4.1. 比较 finalStageIndex: 检查选手 A 和 B 到达的最后一个阶段。如果 A 止步于淘汰赛（stage 2），B 止步于小组赛（stage 1），那么 A 的排名一定高于 B。排序结束。
    // 4.2. 进入“级联比较”: 如果 A 和 B 都止步于淘汰赛（finalStageIndex 相同），则进入 for 循环：
    // i = 2 (淘汰赛阶段): 比较 a.ranks[2] 和 b.ranks[2]。如果他们被淘汰的名次不同（例如，一个第9，一个第11），则排序结束，第9名的选手胜出。
    // i = 1 (小组赛阶段): 如果他们在淘汰赛阶段的名次也相同（例如，都是第9名），循环继续。现在比较 a.ranks[1] 和 b.ranks[1]，也就是他们的小组赛排名。如果 A 的小组排名是第3，B 是第5，则 A 胜出，排序结束。
    // i = 0 (初始排名阶段): 如果他们连小组赛排名都完全一样，循环继续。比较 a.ranks[0] 和 b.ranks[0]，即他们的初始种子排名。
    // 如果所有阶段的排名都完全相同，则返回 0，保持他们的相对位置。
    enrichedFencers.sort((a: any, b: any) => {
      // 规则1: 比较最后达到的阶段 (越高越好)
      if (a.finalStageIndex !== b.finalStageIndex) {
        return b.finalStageIndex - a.finalStageIndex;
      }

      // 规则2: 【级联比较】如果最终阶段相同，则从该阶段开始，逐级向上回溯比较排名
      for (let i = a.finalStageIndex; i >= 0; i--) {
        const rankA = a.ranks[i] ?? 999;
        const rankB = b.ranks[i] ?? 999;

        if (rankA !== rankB) {
          // 在第 i 阶段找到了差异，以此为准，排名数字小者胜
          return rankA - rankB;
        }
      }

      // 如果回溯到 stage 0 依然完全相同，则他们是真正意义上的平手
      return 0;
    });

    // 5.【智能排名分配】(不变)
    finalResults.value = enrichedFencers.map((fencer, index) => {
      let displayRank = index + 1;
      if (!hasBronzeMedalMatch && index === 3) {
        displayRank = 3;
      }
      return {...fencer, displayRank: displayRank};
    });

  } catch (e) {
    console.error("计算最终排名时出错:", e);
    ElMessage.error("生成最终排名失败，请检查控制台。")
  } finally {
    loading.value = false;
  }
}

// 辅助函数保持不变或简化
const getMedalClass = (rank: number) => {
  if (rank === 1) return 'gold'
  if (rank === 2) return 'silver'
  if (rank === 3) return 'bronze'
  return ''
}

const exportToExcel = () => {
  ElMessage.info('导出功能开发中...')
}
const publishResult = () => {
  ElMessage.info('发布功能开发中...')
}

watch(() => props.eventInfo, (newEventInfo) => {
  // 当 eventInfo 变化时，检查它是否包含了我们需要的数据
  if (newEventInfo && newEventInfo.live_ranking && newEventInfo.live_ranking.length > 0) {
    // 如果数据有效，则触发计算
    calculateFinalRanking(newEventInfo);
  }
}, {
  deep: true,      // 深度监视，确保对象内部变化也能被捕获
  immediate: true  // 立即执行一次，处理数据已经存在的情况
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
    color: #409eff;
    font-weight: bold;
    font-family: 'Courier New', Courier, monospace;
  }

  .footer-note {
    margin-top: 20px;
    font-size: 12px;
    color: #909399;
    font-style: italic;
  }
}
</style>
