<template>
  <div class="orchestrator-layout">
    <AppHeader :showCreate="false">
      <template #extra>
        <el-breadcrumb separator-class="el-icon-arrow-right" class="header-breadcrumb">
          <el-breadcrumb-item :to="{ path: '/' }">{{ $t('tournament.dashboard.breadcrumb.home') }}</el-breadcrumb-item>
          <el-breadcrumb-item :to="{ path: '/tournament' }">{{
              $t('tournament.dashboard.breadcrumb.tournamentList')
            }}
          </el-breadcrumb-item>

          <!-- 【关键修复】使用从 eventInfo 中获取的真实 tournament_id -->
          <el-breadcrumb-item :to="{ path: `/tournament/${eventInfo.tournament_id}` }">
            {{ eventInfo.tournament_name || '当前赛事' }}
          </el-breadcrumb-item>

          <el-breadcrumb-item>{{ eventInfo.event_name }}</el-breadcrumb-item>
        </el-breadcrumb>
      </template>
      <template #user>
        <div class="orchestrator-actions">
          <el-button type="info" link icon="Printer">打印表单</el-button>
          <el-divider direction="vertical"/>
          <el-button type="primary" icon="UploadFilled">同步数据</el-button>
          <el-divider direction="vertical"/>
          <el-avatar :size="24" src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png"/>
        </div>
      </template>
    </AppHeader>

    <div class="main-content">
      <!-- ... (aside 和 main 区域保持不变) ... -->
      <aside class="steps-aside">
        <div class="event-meta-card">
          <p class="label">当前规则</p>
          <el-tag size="small" type="warning" effect="light">{{ eventInfo.rule_name }}</el-tag>
        </div>
        <el-steps direction="vertical" :active="currentStep" finish-status="success">
          <el-step
              v-for="(step, index) in steps"
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
              <h2>{{ steps[currentStep].title }}</h2>
            </div>
            <p>{{ steps[currentStep].desc }}</p>
          </header>
          <section class="step-body">
            <transition name="fade-transform" mode="out-in">
              <component
                  :is="steps[currentStep].component"
                  :event-id="eventId"
                  @imported="handleImported"
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
import {ref, onMounted, watch} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {DataManager} from '@/services/DataManager'
import {ElMessage} from 'element-plus'
import AppHeader from '@/components/layout/AppHeader.vue'

// (组件导入保持不变)
import FencerImport from '@/components/tournament/FencerImport.vue'
import PoolGeneration from '@/components/tournament/PoolGeneration.vue'
import PoolScoring from '@/components/tournament/PoolScoring.vue'
import PoolRanking from '@/components/tournament/PoolRanking.vue'
import DETree from '@/components/tournament/DETree.vue'
import FinalRanking from '@/components/tournament/FinalRanking.vue'

const route = useRoute()
const router = useRouter()
const eventId = route.params.id as string

// 【关键修复】改造 eventInfo，让它能存储更完整的上下文信息
const eventInfo = ref<any>({
  event_name: '加载中...',
  rule_name: '',
  tournament_id: '', // 父赛事ID
  tournament_name: '', // 父赛事名称
})

const currentStep = ref(0)
const steps = [
  {title: '选手名单', desc: '导入并确认参赛选手，设置初始种子排名', component: FencerImport},
  {title: '小组赛分组', desc: '根据排名自动进行蛇形分组', component: PoolGeneration},
  {title: '小组赛计分', desc: '录入小组赛矩阵比分，实时计算晋级名额', component: PoolScoring},
  {title: '小组赛排名', desc: '小组赛排名，计算晋级名额', component: PoolRanking},
  {title: '淘汰赛对阵', desc: '生成并管理 DE 淘汰赛对阵图', component: DETree},
  {title: '最终排名', desc: '导出最终成绩册与积分', component: FinalRanking}
]

// 【关键修复】在 onMounted 中获取完整的赛事和项目信息
onMounted(async () => {
  if (eventId) {
    const eventData = await DataManager.getEventById(eventId);
    if (eventData && eventData.tournament_id) {
      // 1. 获取项目自身信息
      eventInfo.value = {...eventInfo.value, ...eventData};

      // 2. 顺藤摸瓜，获取父赛事的信息（主要是名字）
      const tournamentData = await DataManager.getTournamentById(eventData.tournament_id);
      if (tournamentData) {
        eventInfo.value.tournament_name = tournamentData.tournament_name;
      }

      // 3. 恢复步骤
      if (typeof eventData.current_step === 'number') {
        currentStep.value = eventData.current_step;
      }
    } else {
      ElMessage.error('未找到项目信息或项目关联错误');
      router.push('/tournament'); // 如果找不到，返回赛事列表页
    }
  }
});

// watch 逻辑保持不变
watch(currentStep, (newStepIndex) => {
  if (eventId) {
    DataManager.saveCurrentStep(eventId, newStepIndex);
  }
});

const nextStep = () => {
  if (currentStep.value < steps.length - 1) currentStep.value++
}
const prevStep = () => {
  if (currentStep.value > 0) currentStep.value--
}
const handleStepClick = (index: number) => {
  currentStep.value = index
}

// 处理导入成功后，可能需要刷新 eventInfo 的情况
const handleImported = async () => {
  // 可以在这里重新加载 eventData，以更新选手数量等信息
  // await DataManager.getEventById(eventId);
  nextStep(); // 导入成功后自动进入下一步
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
