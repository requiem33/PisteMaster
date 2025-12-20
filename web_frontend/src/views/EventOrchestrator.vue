<template>
  <div class="orchestrator-layout">
    <nav class="top-nav">
      <div class="left">
        <el-button icon="ArrowLeft" circle @click="router.back()"/>
        <span class="event-title">{{ eventInfo.event_name }}</span>
        <el-tag size="small" effect="plain">{{ eventInfo.rule_name }}</el-tag>
      </div>
      <div class="right">
        <el-button type="info" link icon="Printer">打印当前表单</el-button>
        <el-divider direction="vertical"/>
        <el-button type="primary" icon="UploadFilled">同步至服务器</el-button>
      </div>
    </nav>

    <div class="main-content">
      <aside class="steps-aside">
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
            <h2>{{ steps[currentStep].title }}</h2>
            <p>{{ steps[currentStep].desc }}</p>
          </header>

          <section class="step-body">
            <transition name="fade-transform" mode="out-in">
              <keep-alive>
                <component
                    :is="currentStepComponent"
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
/* 路径：src/views/EventOrchestrator.vue */
import {ref, computed, shallowRef} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {ArrowLeft, Printer, UploadFilled} from '@element-plus/icons-vue'

// 导入步骤组件
import FencerImport from '@/components/tournament/FencerImport.vue'
// 下面这些组件我们随后逐一实现
// import PoolGeneration from '@/components/tournament/PoolGeneration.vue'
// import PoolScoring from '@/components/tournament/PoolScoring.vue'

const route = useRoute()
const router = useRouter()
const eventId = route.params.id as string

// 模拟单项信息
const eventInfo = ref({
  event_name: '男子重剑个人赛 (ME)',
  rule_name: 'FIE 标准规则'
})

const currentStep = ref(0)

const steps = [
  {title: '选手名单', desc: '导入并确认参赛选手，设置初始种子排名', component: FencerImport},
  {title: '小组赛分组', desc: '根据排名自动进行蛇形分组', component: null}, // 待实现
  {title: '小组赛计分', desc: '录入小组赛矩阵比分，实时计算晋级名额', component: null},
  {title: '淘汰赛对阵', desc: '生成并管理 DE 淘汰赛对阵图', component: null},
  {title: '最终排名', desc: '导出最终成绩册与积分', component: null}
]

// 动态获取当前组件
const currentStepComponent = computed(() => steps[currentStep.value].component)

const nextStep = () => {
  if (currentStep.value < steps.length - 1) {
    currentStep.value++
  }
}

const handleStepClick = (index: number) => {
  // 仅允许点击已完成或当前的步骤
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
  background-color: #f0f2f5;

  .top-nav {
    height: 50px;
    background: #fff;
    border-bottom: 1px solid #dcdfe6;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 20px;

    .left {
      display: flex;
      align-items: center;
      gap: 15px;

      .event-title {
        font-weight: bold;
        font-size: 16px;
      }
    }
  }

  .main-content {
    flex: 1;
    display: flex;
    overflow: hidden;

    .steps-aside {
      width: 200px;
      background: #fff;
      padding: 30px 20px;
      border-right: 1px solid #dcdfe6;

      .step-item {
        cursor: pointer;
        transition: 0.3s;
      }
    }

    .work-area {
      flex: 1;
      padding: 24px;
      overflow-y: auto;

      .step-card {
        background: #fff;
        min-height: 100%;
        border-radius: 8px;
        box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
        display: flex;
        flex-direction: column;

        .step-header {
          padding: 20px 30px;
          border-bottom: 1px solid #f0f2f5;

          h2 {
            margin: 0;
            font-size: 20px;
          }

          p {
            margin: 8px 0 0;
            color: #909399;
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
}

/* 步骤切换动画 */
.fade-transform-enter-active,
.fade-transform-leave-active {
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