<!-- src/views/EventOrchestrator.vue -->
<template>
  <div class="orchestrator-layout">
    <AppHeader :showCreate="false">
      <template #extra>
        <el-breadcrumb separator-class="el-icon-arrow-right" class="header-breadcrumb">
          <el-breadcrumb-item :to="{ path: '/' }">{{ $t('tournament.dashboard.breadcrumb.home') }}</el-breadcrumb-item>
          <el-breadcrumb-item :to="{ path: '/tournament' }">{{ $t('tournament.dashboard.breadcrumb.tournamentList') }}</el-breadcrumb-item>
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
          <p class="label">{{ $t('event.currentRule') }}</p>
          <el-tag size="small" type="warning" effect="light">{{ eventInfo.rule_name }}</el-tag>
        </div>

        <el-steps direction="vertical" :active="currentStep" finish-status="success">
          <el-step
              v-for="(step, index) in computedSteps"
              :key="step.id"
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
              <component
                  :is="computedSteps[currentStep]?.component"
                  :key="computedSteps[currentStep]?.id"
                  :event-id="eventId"
                  :event-info="eventInfo"
                  :stage-config="computedSteps[currentStep]?.stageConfig"
                  :stage-index="computedSteps[currentStep]?.stageIndex"
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
import {useRoute} from 'vue-router'
import {useI18n} from 'vue-i18n'
import {DataManager} from '@/services/DataManager'
import {ElMessage} from 'element-plus'
import AppHeader from '@/components/layout/AppHeader.vue'

import FencerImport from '@/components/tournament/FencerImport.vue'
import PoolGeneration from '@/components/tournament/PoolGeneration.vue'
import PoolScoring from '@/components/tournament/PoolScoring.vue'
import PoolRanking from '@/components/tournament/PoolRanking.vue'
import DETree from '@/components/tournament/DETree.vue'
import FinalRanking from '@/components/tournament/FinalRanking.vue'

const {t} = useI18n()
const route = useRoute()
const eventId = route.params.id as string

const eventInfo = ref<any>({
  event_name: '',
  tournament_id: '',
  tournament_name: '',
  rules: {stages: []}
})
const currentStep = ref(0)

const computedSteps = computed(() => {
  const steps: any[] = [];

  steps.push({
    id: 'import',
    title: t('event.steps.fencerList'),
    desc: t('event.stepDescriptions.fencerList'),
    component: FencerImport,
    stageIndex: 0
  });

  const stages = eventInfo.value.rules?.stages || [];

  stages.forEach((stage: any, index: number) => {
    const stageIndex = index + 1;
    const stageId = `stage_${index}_${stage.type}`;
    const stageConfigWithId = {...stage, id: stageId};

    if (stage.type === 'pool') {
      steps.push({
        id: `${stageId}_gen`,
        title: t('event.stageN', {n: stageIndex}) + ': ' + t('event.steps.poolGeneration'),
        desc: t('event.stepDescriptions.poolGeneration', {n: stageIndex}),
        component: PoolGeneration,
        stageConfig: stageConfigWithId, stageIndex
      });
      steps.push({
        id: `${stageId}_score`,
        title: t('event.stageN', {n: stageIndex}) + ': ' + t('event.steps.poolScoring'),
        desc: t('event.stepDescriptions.poolScoring', {n: stageIndex}),
        component: PoolScoring,
        stageConfig: stageConfigWithId, stageIndex
      });
      steps.push({
        id: `${stageId}_rank`,
        title: t('event.stageN', {n: stageIndex}) + ': ' + t('event.steps.poolRanking'),
        desc: t('event.stepDescriptions.poolRanking', {n: stageIndex}),
        component: PoolRanking,
        stageConfig: stageConfigWithId, stageIndex
      });
    } else if (stage.type === 'de') {
      steps.push({
        id: stageId,
        title: t('event.stageN', {n: stageIndex}) + ': ' + t('event.steps.elimination'),
        desc: t('event.stepDescriptions.elimination', {n: stageIndex}),
        component: DETree,
        stageConfig: stageConfigWithId, stageIndex
      });
    }
  });

  steps.push({
    id: 'final_rank',
    title: t('event.steps.finalRanking'),
    desc: t('event.ranking.exportResults'),
    component: FinalRanking,
    stageIndex: stages.length + 1
  });

  return steps;
});

onMounted(async () => {
  if (eventId) {
    const eventData = await DataManager.getEventById(eventId);
    if (eventData) {
      eventInfo.value = {...eventInfo.value, ...eventData};
      if (eventData.rule_info && eventData.rule_info.stages) {
        eventInfo.value.rules = {
          preset: eventData.rule_info.preset_code || 'custom',
          stages: eventData.rule_info.stages
        };
        eventInfo.value.rule_name = eventData.rule_info.rule_name;
      }
      const tournamentId = eventData.tournament_info?.id;
      if (tournamentId) {
        eventInfo.value.tournament_id = tournamentId;
        eventInfo.value.tournament_name = eventData.tournament_info.tournament_name;
      }
      currentStep.value = eventData.current_step || 0;
    } else {
      ElMessage.error(t('common.messages.notFound'));
    }
  }
});

watch(currentStep, (newStepIndex) => {
  if (eventId) {
    DataManager.saveCurrentStep(eventId, newStepIndex);
  }
});

const nextStep = () => {
  if (currentStep.value < computedSteps.value.length - 1) {currentStep.value++}
}
const prevStep = () => {
  if (currentStep.value > 0) {currentStep.value--}
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
