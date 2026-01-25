<template>
  <div class="final-ranking-container">
    <div class="ranking-actions">
      <el-alert
          title="赛事已结束"
          type="success"
          description="所有成绩已根据 FIE 标准规则计算完成。您可以导出成绩单或发布最终成绩。"
          show-icon
          :closable="false"
      />
      <div class="buttons">
        <el-button type="primary" icon="Download" @click="exportToExcel">导出成绩单 (Excel)</el-button>
        <el-button type="warning" icon="Share" @click="publishResult">发布成绩至大屏幕</el-button>
      </div>
    </div>

    <el-card shadow="never" class="table-card">
      <el-table :data="finalResults" border stripe style="width: 100%" v-loading="loading">
        <el-table-column label="名次" width="80" align="center">
          <template #default="scope">
            <div :class="['rank-badge', getMedalClass(scope.$index + 1)]">
              {{ scope.$index + 1 }}
            </div>
          </template>
        </el-table-column>

        <el-table-column label="选手 (Fencers)" min-width="180">
          <template #default="scope">
            <div class="fencer-cell">
              <span class="full-name">{{ scope.row.last_name }} {{ scope.row.first_name }}</span>
              <el-tag size="small" effect="plain" class="club-tag">{{ scope.row.club || '个人' }}</el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="country_code" label="地区/国籍" width="100" align="center"/>

        <el-table-column label="小组赛表现" align="center">
          <el-table-column label="V/M" width="80" align="center">
            <template #default="scope">{{ scope.row.v_m.toFixed(3) }}</template>
          </el-table-column>
          <el-table-column prop="ind" label="Ind." width="70" align="center"/>
        </el-table-column>

        <el-table-column label="最后轮次" width="150" align="center">
          <template #default="scope">
            <!-- 【修改】调用新的辅助函数 -->
            <el-tag :type="getRoundTagType(scope.row)">
              {{ getRoundText(scope.row, eventInfo?.rules?.stages || []) }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 获得积分列可以暂时移除，或根据赛事级别配置 -->

      </el-table>
    </el-card>

    <div class="footer-note">
      \* 最终排名计算规则：根据淘汰赛被淘汰轮次排序，同轮次淘汰者按照小组赛成绩排序。
    </div>
  </div>
</template>

<script setup lang="ts">
import {ref, onMounted, computed} from 'vue'
import {DataManager} from '@/services/DataManager'
import {ElMessage} from 'element-plus'
import type {Stage} from '@/types'; // 引入类型，如果还没有

const props = defineProps<{
  eventId: string,
  eventInfo: any // 接收完整的 event 对象
}>()

const finalResults = ref<any[]>([])
const loading = ref(false)

/**
 * 【核心改造】重写数据加载与计算逻辑
 */
const loadFinalRanking = async () => {
  loading.value = true;
  try {
    const event = await DataManager.getEventById(props.eventId);
    if (!event || !event.live_ranking) {
      ElMessage.warning("没有找到有效的排名记录");
      return;
    }

    const stages: Stage[] = event.rules?.stages || [];

    // 1. 获取小组赛阶段的详细赛果，用于最终的 tie-breaker 和数据展示
    const poolStage = stages.findLast(s => s.type === 'pool');
    const poolResults = poolStage ? await DataManager.getEventPoolRanking(poolStage.id) : [];
    const poolResultsMap = new Map(poolResults.map(r => [r.id, r]));
    const poolStageIndex = poolStage ? stages.indexOf(poolStage) + 1 : 0;

    // 2.【“历史学家”逻辑】遍历 live_ranking，富集每个选手的数据
    const enrichedFencers = event.live_ranking.map((fencer: any) => {
      const stageKeys = Object.keys(fencer.ranks).map(Number);
      const finalStageIndex = Math.max(...stageKeys);

      const finalRankInStage = fencer.ranks[finalStageIndex];
      const wasEliminated = fencer.elimination_status[finalStageIndex];

      const poolStats = poolResultsMap.get(fencer.id) || {v_m: 0, ind: 0, ts: 0, tr: 0};
      const poolRank = fencer.ranks[poolStageIndex] || 999; // 小组排名作为 tie-breaker

      return {
        ...fencer,
        ...poolStats,
        finalStageIndex,
        finalRankInStage,
        wasEliminated,
        poolRank,
      };
    });

    // 3.【最终排序】
    enrichedFencers.sort((a: any, b: any) => {
      // 规则1: 比较最后达到的阶段 (越高越好)
      if (a.finalStageIndex !== b.finalStageIndex) {
        return b.finalStageIndex - a.finalStageIndex;
      }
      // 规则2: 比较在同一阶段的名次 (越小越好)
      if (a.finalRankInStage !== b.finalRankInStage) {
        return a.finalRankInStage - b.finalRankInStage;
      }
      // 规则3: 平分决胜局 - 比较小组赛排名 (越小越好)
      return a.poolRank - b.poolRank;
    });

    finalResults.value = enrichedFencers;

  } catch (error) {
    console.error("加载最终排名失败:", error);
    ElMessage.error("无法生成最终排名");
  } finally {
    loading.value = false;
  }
};

/**
 * 【辅助函数】根据选手的最终状态，生成人类可读的轮次描述
 */
const getRoundTagType = (fencer: any) => {
  // 这里的实现可以更精确，例如判断是否为冠军、亚军等
  if (fencer.finalRankInStage <= 3 && !fencer.wasEliminated) {
    if (fencer.finalRankInStage === 1) return 'danger'; // Gold
    if (fencer.finalRankInStage === 2) return 'primary'; // Silver
    if (fencer.finalRankInStage === 3) return 'warning'; // Bronze
  }
  return 'info';
}

const getRoundText = (fencer: any, stages: Stage[]) => {
  const finalStage = stages[fencer.finalStageIndex - 1];
  if (!finalStage) return "初始排名";

  if (!fencer.wasEliminated) {
    if (fencer.finalRankInStage === 1) return "冠军";
    if (fencer.finalRankInStage === 2) return "亚军";
    if (fencer.finalRankInStage === 3) return "季军";
  }

  return `止步 ${finalStage.name}`;
}

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
  loadFinalRanking();
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
