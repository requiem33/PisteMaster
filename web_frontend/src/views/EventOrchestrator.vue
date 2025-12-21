<template>
  <div class="orchestrator-layout">
    <AppHeader :title="eventInfo.event_name" :showCreate="false">
      <template #extra>
        <el-breadcrumb separator-class="el-icon-arrow-right" class="header-breadcrumb">
          <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
          <el-breadcrumb-item :to="{ path: '/tournament' }">赛事列表</el-breadcrumb-item>
          <el-breadcrumb-item :to="{ path: `/tournament/${tournamentId}` }">赛事控制台</el-breadcrumb-item>
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
              <keep-alive>
                <component
                    :is="steps[currentStep].component"
                    :event-id="eventId"
                    @next="nextStep"
                />
              </keep-alive>
            </transition>
          </section>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import {ref} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {Printer, UploadFilled, ArrowLeft} from '@element-plus/icons-vue'
import AppHeader from '@/components/layout/AppHeader.vue'

// 导入步骤子组件
import FencerImport from '@/components/tournament/FencerImport.vue'
import PoolGeneration from '@/components/tournament/PoolGeneration.vue'
import PoolScoring from '@/components/tournament/PoolScoring.vue'
import PoolRanking from '@/components/tournament/PoolRanking.vue'
import DETree from '@/components/tournament/DETree.vue'
import FinalRanking from '@/components/tournament/FinalRanking.vue'

const route = useRoute()
const router = useRouter()
const eventId = route.params.id as string
const tournamentId = ref('t1') // 实际应从 API 或路由 query 获取

// 模拟单项信息
const eventInfo = ref({
  event_name: '男子重剑个人赛 (ME)',
  rule_name: 'FIE 标准规则'
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

const nextStep = () => {
  if (currentStep.value < steps.length - 1) currentStep.value++
}
const prevStep = () => {
  if (currentStep.value > 0) currentStep.value--
}

const handleStepClick = (index: number) => {
  // 逻辑：允许自由回看已完成的步骤
  if (index <= currentStep.value + 1) {
    currentStep.value = index
  }
}
</script>

<style scoped lang="scss">
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

  .steps-aside {
    width: 220px;
    background: var(--el-bg-color);
    padding: 20px;
    border-right: 1px solid var(--el-border-color-light);
    display: flex;
    flex-direction: column;
    gap: 20px;

    .event-meta-card {
      padding: 15px;
      background: var(--el-fill-color-light);
      border-radius: 8px;

      .label {
        font-size: 12px;
        color: var(--el-text-color-secondary);
        margin-bottom: 8px;
      }
    }

    .step-item {
      cursor: pointer;
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
          margin: 10px 0 0 44px; /* 对齐标题文字 */
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
}

/* 动画保持不变 */
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