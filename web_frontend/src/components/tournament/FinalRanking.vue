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
import {ref, onMounted} from 'vue'
import {ElMessage} from 'element-plus'
import type {Stage} from '@/types';

// 接收父组件传递的 eventInfo
const props = defineProps<{
  eventId: string,
  eventInfo: any
}>()

const finalResults = ref<any[]>([])
const loading = ref(false)

const calculateFinalRanking = () => {
  if (!props.eventInfo || !props.eventInfo.live_ranking) {
    ElMessage.warning("没有找到有效的排名记录");
    return;
  }
  loading.value = true;

  try {
    const stages: Stage[] = props.eventInfo.rules?.stages || [];
    const liveRanking = props.eventInfo.live_ranking;

    // 1. 【读取配置】确定季军赛规则
    const lastStage = stages.length > 0 ? stages[stages.length - 1] : null;
    const hasBronzeMedalMatch = lastStage?.type === 'de' && lastStage.config?.final_stage === 'bronze_medal';

    // 2.【“富集”逻辑】
    const enrichedFencers = liveRanking.map((fencer: any) => {
      const stageKeys = Object.keys(fencer.ranks).map(Number);
      const finalStageIndex = Math.max(...stageKeys, 0);
      const finalRankInStage = fencer.ranks[finalStageIndex] ?? 999;
      const poolRank = fencer.ranks[stages.findIndex(s => s.type === 'pool') + 1] || 999;

      return {
        ...fencer,
        finalStageIndex,
        finalRankInStage,
        poolRank,
      };
    });

    // 3.【排序逻辑】(保持不变)
    enrichedFencers.sort((a: any, b: any) => {
      if (a.finalStageIndex !== b.finalStageIndex) return b.finalStageIndex - a.finalStageIndex;
      if (a.finalRankInStage !== b.finalRankInStage) return a.finalRankInStage - b.finalRankInStage;
      return a.poolRank - b.poolRank;
    });

    // 4.【智能排名分配】(核心改造)
    finalResults.value = enrichedFencers.map((fencer, index) => {
      let displayRank = index + 1;
      // 如果没有季军赛 (即并列第三)，并且当前正在处理第四名 (index === 3)
      if (!hasBronzeMedalMatch && index === 3) {
        // 强制将其名次设为 3
        displayRank = 3;
      }
      return {
        ...fencer,
        displayRank: displayRank
      };
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

onMounted(() => {
  calculateFinalRanking();
})
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
