<template>
  <el-container class="layout-container">
    <el-header class="app-header">
      <div class="logo">PisteMaster <span>Orchestrator</span></div>
      <div class="tournament-info">
        <el-tag type="success" effect="dark">ME - 男子重剑个人赛</el-tag>
        <span class="sync-status"><el-icon><Refresh/></el-icon> 已同步</span>
      </div>
      <div class="user-actions">
        <el-button type="primary" plain icon="Printer">打印报表</el-button>
        <el-avatar :size="32" src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png"/>
      </div>
    </el-header>

    <el-container>
      <el-aside width="240px" class="app-aside">
        <el-steps direction="vertical" :active="activeStep" finish-status="success">
          <el-step v-for="(step, index) in workflowSteps"
                   :key="index"
                   :title="step.title"
                   @click="activeStep = index"
                   class="clickable-step"/>
        </el-steps>
      </el-aside>

      <el-main class="app-main">
        <div class="content-card">
          <div class="step-header">
            <h2>{{ workflowSteps[activeStep].title }}</h2>
            <p class="subtitle">{{ workflowSteps[activeStep].description }}</p>
          </div>

          <el-divider/>

          <div class="step-body">
            <div class="placeholder-content">
              <el-empty :description="`正在开发: ${workflowSteps[activeStep].title} 模块`"/>
            </div>
          </div>

          <div class="step-footer">
            <el-button @click="activeStep--" :disabled="activeStep === 0">上一步</el-button>
            <el-button type="primary" @click="activeStep++" :disabled="activeStep === workflowSteps.length - 1">
              保存并进入下一步
            </el-button>
          </div>
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import {ref} from 'vue'

const activeStep = ref(0)

const workflowSteps = [
  {title: '赛事基础配置', description: '设置比赛名称、时间、地点及击剑规则'},
  {title: '选手报名管理', description: '导入选手、检查资格、确认种子排名'},
  {title: '小组赛分组', description: '自动或手动进行小组蛇形分配'},
  {title: '小组赛计分', description: '录入小组赛矩阵比分'},
  {title: '晋级名单确认', description: '根据小组赛成绩计算排名及淘汰赛位'},
  {title: '淘汰赛对阵', description: '生成并管理 DE 对阵表'},
  {title: '最终成绩发布', description: '生成最终排名并导出官方成绩单'}
]
</script>

<style lang="scss">
body {
  margin: 0;
  font-family: 'Inter', sans-serif;
  background-color: #f5f7fa;
}

.layout-container {
  height: 100vh;
}

.app-header {
  background-color: #1a1a1a;
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid #333;

  .logo {
    font-weight: bold;
    font-size: 1.2rem;

    span {
      color: #409eff;
    }
  }
}

.app-aside {
  background: white;
  border-right: 1px solid #e6e6e6;
  padding: 40px 20px;

  .clickable-step {
    cursor: pointer;

    &:hover {
      opacity: 0.8;
    }
  }
}

.app-main {
  padding: 24px;

  .content-card {
    background: white;
    border-radius: 8px;
    height: 100%;
    display: flex;
    flex-direction: column;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
    padding: 30px;
  }

  .step-header {
    h2 {
      margin: 0;
      font-size: 1.5rem;
    }

    .subtitle {
      color: #909399;
      margin-top: 8px;
    }
  }

  .step-body {
    flex: 1;
    overflow-y: auto;
    padding: 20px 0;
  }

  .step-footer {
    border-top: 1px solid #f0f0f0;
    padding-top: 20px;
    display: flex;
    justify-content: space-between;
  }
}
</style>