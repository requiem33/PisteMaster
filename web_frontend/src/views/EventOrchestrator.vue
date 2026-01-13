<template>
  <div class="orchestrator-layout">
    <AppHeader :showCreate="false">
      <!-- Header 内容保持不变 -->
      <template #extra>
        <el-breadcrumb separator-class="el-icon-arrow-right" class="header-breadcrumb">
          <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
          <el-breadcrumb-item :to="{ path: '/tournament' }">赛事列表</el-breadcrumb-item>
          <el-breadcrumb-item :to="{ path: `/tournament/${eventInfo.tournament_id}` }">{{
              eventInfo.tournament_name
            }}
          </el-breadcrumb-item>
          <el-breadcrumb-item>{{ eventInfo.event_name }}</el-breadcrumb-item>
        </el-breadcrumb>
      </template>
    </AppHeader>

    <div class="main-content">
      <aside class="steps-aside">
        <div class="event-meta-card">
          <p class="label">当前规则</p>
          <el-tag size="small" type="warning" effect="light">{{ eventInfo.rule_name }}</el-tag>
        </div>

        <el-steps direction="vertical" :active="currentStep" finish-status="success">
          <el-step
              v-for="(step, index) in computedSteps"
              :key="index"
              :title="step.title"
              @click="handleStepClick(index)"
              class="step-item"
          />
        </el-steps>
      </aside>

      <main class="work-area">
        <div class="step-card">
          <header class="step-header">
            <div class="title-group">
              <el-button icon="ArrowLeft" circle size="small" @click="prevStep" :disabled="currentStep === 0"/>
              <h2>{{ computedSteps[currentStep]?.title }}</h2>
            </div>
            <p>{{ computedSteps[currentStep]?.desc }}</p>
          </header>

          <section class="step-body">
            <transition name="fade-transform" mode="out-in">
              <!-- 动态组件渲染，并将当前的 stage 配置传入 -->
              <component
                  :is="computedSteps[currentStep]?.component"
                  :event-id="eventId"
                  :stage-config="computedSteps[currentStep]?.stageData"
                  @next="nextStep"
              />
            </transition>
          </section>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import {ref, onMounted, watch, computed} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {DataManager} from '@/services/DataManager'
import {ElMessage} from 'element-plus'
import AppHeader from '@/components/layout/AppHeader.vue'

// 导入所有可能用到的子组件
import FencerImport from '@/components/tournament/FencerImport.vue'
import PoolGeneration from '@/components/tournament/PoolGeneration.vue'
import PoolScoring from '@/components/tournament/PoolScoring.vue'
import PoolRanking from '@/components/tournament/PoolRanking.vue'
import DETree from '@/components/tournament/DETree.vue'
import FinalRanking from '@/components/tournament/FinalRanking.vue'

const route = useRoute()
const eventId = route.params.id as string

const eventInfo = ref<any>({
  event_name: '加载中...',
  tournament_id: '',
  tournament_name: '',
  rules: {stages: []} // 核心规则数据
})
const currentStep = ref(0)

// 基础步骤（所有比赛都有）
const baseSteps = {
  import: {title: '选手名单', desc: '导入并确认参赛选手，设置初始种子排名', component: FencerImport},
  final: {title: '最终排名', desc: '导出最终成绩册与积分', component: FinalRanking}
}

// 核心逻辑：根据 rules.stages 动态生成步骤链
const computedSteps = computed(() => {
  const steps: any[] = [];

  // 1. 第一步永远是选手名单
  steps.push(baseSteps.import);

  // 2. 遍历 stages 数组，动态插入中间步骤
  const stages = eventInfo.value.rules?.stages || [];

  stages.forEach((stage: any, index: number) => {
    const stageNum = index + 1;

    if (stage.type === 'pool') {
      // 小组赛包含三个子步骤
      steps.push({
        title: `阶段${stageNum}: 小组分组`,
        desc: `第${stageNum}阶段小组循环赛 - 自动蛇形分组 (Config: Byes ${stage.config.byes})`,
        component: PoolGeneration,
        stageData: stage // 将配置透传给组件
      });
      steps.push({
        title: `阶段${stageNum}: 小组计分`,
        desc: `第${stageNum}阶段小组循环赛 - 录入比分`,
        component: PoolScoring,
        stageData: stage
      });
      steps.push({
        title: `阶段${stageNum}: 小组排名`,
        desc: `第${stageNum}阶段小组循环赛 - 晋级计算 (Elimination: ${stage.config.elimination_rate}%)`,
        component: PoolRanking,
        stageData: stage
      });
    } else if (stage.type === 'de') {
      // 淘汰赛只有一个步骤
      steps.push({
        title: `阶段${stageNum}: 淘汰赛表`,
        desc: `第${stageNum}阶段单败淘汰赛 - (Final: ${stage.config.final_stage})`,
        component: DETree,
        stageData: stage
      });
    }
  });

  // 3. 最后一步永远是最终排名
  steps.push(baseSteps.final);

  return steps;
});

onMounted(async () => {
  if (eventId) {
    const eventData = await DataManager.getEventById(eventId);
    if (eventData) {
      eventInfo.value = {...eventInfo.value, ...eventData};

      const tournamentData = await DataManager.getTournamentById(eventData.tournament_id);
      if (tournamentData) {
        eventInfo.value.tournament_name = tournamentData.tournament_name;
      }
      currentStep.value = eventData.current_step || 0;
    } else {
      ElMessage.error('未找到项目信息');
    }
  }
});

watch(currentStep, (newStepIndex) => {
  if (eventId) {
    DataManager.saveCurrentStep(eventId, newStepIndex);
  }
});

const nextStep = () => {
  if (currentStep.value < computedSteps.value.length - 1) currentStep.value++
}
const prevStep = () => {
  if (currentStep.value > 0) currentStep.value--
}
const handleStepClick = (index: number) => {
  currentStep.value = index
}
</script>

<style scoped lang="scss">
/* 样式部分保持不变 */
.orchestrator-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--el-bg-color-page);
}

.header-breadcrumb {
  margin-left: 10px;
  font-size: 13px;
}

.orchestrator-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.steps-aside {
  width: 240px;
  background: var(--el-bg-color);
  padding: 20px;
  border-right: 1px solid var(--el-border-color-light);

  .event-meta-card {
    padding: 15px;
    background: var(--el-fill-color-light);
    border-radius: 8px;
    margin-bottom: 30px;

    .label {
      font-size: 12px;
      color: var(--el-text-color-secondary);
      margin-bottom: 8px;
    }
  }

  .el-steps {
    height: auto !important;
  }

  .step-item {
    cursor: pointer;

    :deep(.el-step__main) {
      padding-bottom: 32px;
    }

    &:hover :deep(.el-step__title) {
      color: var(--el-color-primary);
    }
  }
}

.work-area {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: var(--el-fill-color-blank);

  .step-card {
    background: var(--el-bg-color);
    min-height: 100%;
    border-radius: 12px;
    border: 1px solid var(--el-border-color-light);
    display: flex;
    flex-direction: column;

    .step-header {
      padding: 24px 30px;
      border-bottom: 1px solid var(--el-border-color-lighter);

      .title-group {
        display: flex;
        align-items: center;
        gap: 12px;

        h2 {
          margin: 0;
          font-size: 22px;
          font-weight: 600;
        }
      }

      p {
        margin: 10px 0 0 44px;
        color: var(--el-text-color-secondary);
        font-size: 14px;
      }
    }

    .step-body {
      flex: 1;
      padding: 30px;
    }
  }
}

.fade-transform-enter-active, .fade-transform-leave-active {
  transition: all 0.3s;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-15px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(15px);
}
</style>
