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
            <el-tag :type="getRoundTagType(scope.row.last_round)">
              {{ scope.row.last_round }}
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
import {ref, onMounted} from 'vue'
import {DataManager} from '@/services/DataManager'
import {ElMessage} from 'element-plus'

const props = defineProps<{ eventId: string }>()

const finalResults = ref<any[]>([])
const loading = ref(false)

const loadFinalRanking = async () => {
  loading.value = true;
  try {
    const results = await DataManager.getFinalRanking(props.eventId);
    finalResults.value = results;
  } catch (error) {
    console.error("加载最终排名失败:", error);
    ElMessage.error("无法生成最终排名");
  } finally {
    loading.value = false;
  }
};

const getMedalClass = (rank: number) => {
  if (rank === 1) return 'gold'
  if (rank === 2) return 'silver'
  if (rank === 3) return 'bronze'
  return ''
}

const getRoundTagType = (round: string) => {
  if (round.includes('冠军') || round.includes('亚军')) return 'danger'
  if (round.includes('季军')) return 'warning'
  if (round.includes('Table of 4')) return 'primary'
  return 'info'
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
