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
      <el-table :data="finalResults" border stripe style="width: 100%">
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

        <el-table-column prop="country_code" label="地区/国籍" width="100" align="center" />

        <el-table-column label="小组赛表现" align="center">
          <el-table-column label="V/M" width="80" align="center">
            <template #default="scope">{{ scope.row.v_m.toFixed(3) }}</template>
          </el-table-column>
          <el-table-column prop="ind" label="Ind." width="70" align="center" />
        </el-table-column>

        <el-table-column label="最后轮次" width="150" align="center">
          <template #default="scope">
            <el-tag :type="getRoundTagType(scope.row.last_round)">
              {{ scope.row.last_round }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="获得积分" width="100" align="center">
          <template #default="scope">
            <span class="points">+{{ scope.row.earned_points }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <div class="footer-note">
      * 最终排名计算规则：根据淘汰赛被淘汰轮次排序，同轮次淘汰者按照小组赛成绩排序。
    </div>
  </div>
</template>

<script setup lang="ts">
/* 路径：src/components/tournament/FinalRanking.vue */
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps<{ eventId: string }>()

// 模拟最终排名数据
// 逻辑：1-4名是决赛和半决赛产生的，5-8名是Table of 8淘汰的，以此类推
const finalResults = ref([
  { last_name: 'KANO', first_name: 'K.', country_code: 'JPN', club: 'Tokyo Club', v_m: 1.000, ind: 15, last_round: '决赛 (Gold)', earned_points: 32 },
  { last_name: 'CHUMAK', first_name: 'D.', country_code: 'UKR', club: 'Kyiv Fencing', v_m: 0.833, ind: 12, last_round: '决赛 (Silver)', earned_points: 26 },
  { last_name: 'SIKLOSI', first_name: 'G.', country_code: 'HUN', club: 'Budapest SC', v_m: 0.833, ind: 10, last_round: '半决赛 (Bronze)', earned_points: 20 },
  { last_name: 'WANG', first_name: 'Z.', country_code: 'CHN', club: '江办省队', v_m: 0.667, ind: 8, last_round: '半决赛 (4th)', earned_points: 18 },
  { last_name: 'BOREL', first_name: 'Y.', country_code: 'FRA', club: 'Levallois', v_m: 0.667, ind: 6, last_round: 'Table of 8', earned_points: 14 },
  { last_name: 'LIMARDO', first_name: 'R.', country_code: 'VEN', club: 'Venezuela', v_m: 0.500, ind: -2, last_round: 'Table of 8', earned_points: 14 },
  { last_name: 'MINOBE', first_name: 'K.', country_code: 'JPN', club: 'Nexus', v_m: 0.500, ind: -5, last_round: 'Table of 8', earned_points: 14 },
  { last_name: 'PARK', first_name: 'S.', country_code: 'KOR', club: 'Seoul SC', v_m: 0.333, ind: -8, last_round: 'Table of 8', earned_points: 14 },
])

const getMedalClass = (rank: number) => {
  if (rank === 1) return 'gold'
  if (rank === 2) return 'silver'
  if (rank === 3) return 'bronze'
  return ''
}

const getRoundTagType = (round: string) => {
  if (round.includes('决赛')) return 'danger'
  if (round.includes('半决赛')) return 'warning'
  return 'info'
}

const exportToExcel = () => {
  ElMessage.success('正在生成 Excel 成绩单...')
}

const publishResult = () => {
  ElMessage({ message: '成绩已同步至公示板', type: 'success' })
}

onMounted(() => {
  // 实际开发中，这里会根据比赛的所有 DE 记录和小组赛记录向后端请求最终排名结果
})
</script>

<style scoped lang="scss">
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

    &.gold { background: #ffd700; color: #fff; text-shadow: 0 1px 2px rgba(0,0,0,0.2); }
    &.silver { background: #c0c0c0; color: #fff; }
    &.bronze { background: #cd7f32; color: #fff; }
  }

  .fencer-cell {
    display: flex;
    flex-direction: column;
    .full-name { font-weight: bold; margin-bottom: 4px; }
    .club-tag { align-self: flex-start; font-size: 10px; }
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