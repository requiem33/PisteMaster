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
  stageConfig: any
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
      loading.value = false;
      return;
    }

    // 【核心修复】调用 DataManager 时传入 stageId
    const [liveFencers, poolResults] = await Promise.all([
      DataManager.getLiveFencers(props.eventId),
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

const sortedRanking = computed(() => {
  if (allFencersForStage.value.length === 0) return []

  const byeCount = props.stageConfig?.config?.byes || 0;
  const eliminationRate = props.stageConfig?.config?.elimination_rate || 20;

  // a. 找出轮空选手，并赋予他们最高优先级
  const byeFencerIds = allFencersForStage.value.slice(0, byeCount).map(f => f.id);
  const byeFencers = allFencersForStage.value
      .filter(f => byeFencerIds.includes(f.id))
      .map(f => ({...f, is_bye: true}));

  // b. 找出并排序参赛选手
  // 确保只处理在 liveFencers 中也存在的选手，防止旧数据干扰
  const activeFencerIds = allFencersForStage.value.slice(byeCount).map(f => f.id);
  const rankedPoolFencers = poolResultsFencers.value
      .filter(f => activeFencerIds.includes(f.id))
      .sort((a, b) => {
        if (b.v_m !== a.v_m) return b.v_m - a.v_m;
        if (b.ind !== a.ind) return b.ind - a.ind;
        return b.ts - a.ts;
      });

  const combinedList = [...byeFencers, ...rankedPoolFencers];

  return combinedList.map((fencer, index) => {
    const qualifiedCount = Math.floor(combinedList.length * (1 - eliminationRate / 100));
    const isQualified = fencer.is_bye || index < qualifiedCount;

    return {
      ...fencer,
      pool_rank: index + 1,
      is_qualified: isQualified
    }
  });
})

const proceedToNextStage = async () => {
  isSaving.value = true;
  try {
    const eliminationRate = props.stageConfig?.config?.elimination_rate || 20;

    // 从 allFencersForStage (live_ranking) 开始，确保所有选手都被包含
    const newLiveRanking = allFencersForStage.value.map(f => {
      const result = sortedRanking.value.find(sr => sr.id === f.id);
      if (result) {
        // 如果选手参与了本轮（或轮空），则更新其状态
        return {
          ...f, // 继承旧信息
          current_rank: result.pool_rank, // 更新排名
          is_eliminated: !result.is_qualified, // 更新淘汰状态
          elimination_round: result.is_qualified ? f.elimination_round : `小组赛`,
          // 更新赛果统计
          v_m: result.v_m,
          ind: result.ind,
          ts: result.ts,
          tr: result.tr,
        };
      }
      // 如果选手在本轮未出现（例如，未来多轮淘汰赛的场景），则保持原样
      return f;
    }).sort((a, b) => a.current_rank - b.current_rank); // 最后按新排名排序

    await DataManager.updateLiveRanking(props.eventId, newLiveRanking);

    ElMessage.success('本阶段排名已保存，新的实时排名已生成');
    emit('next');
  } catch (error) {
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
