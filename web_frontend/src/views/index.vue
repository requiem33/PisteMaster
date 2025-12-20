<template>
  <div class="home-container">
    <div class="top-toolbar">
      <el-switch
          v-model="isDark"
          class="theme-switch"
          inline-prompt
          :active-icon="Moon"
          :inactive-icon="Sunny"
          @change="toggleDark"
      />
      <el-divider direction="vertical"/>
      <el-button v-if="!isLoggedIn" type="primary" link>注册 / 登录</el-button>
      <el-dropdown v-else>
        <span class="user-info">
          <el-avatar :size="24" src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png"/>
          管理员 <el-icon><ArrowDown/></el-icon>
        </span>
        <template #footer>
          <el-dropdown-item>个人中心</el-dropdown-item>
          <el-dropdown-item divided>退出登录</el-dropdown-item>
        </template>
      </el-dropdown>
    </div>

    <el-row class="hero-section">
      <el-col :md="12" class="left-brand">
        <div class="logo-wrapper">
          <el-icon class="main-logo" :size="120" color="#409eff">
            <Odometer/>
          </el-icon>
          <h1 class="brand-title">PisteMaster</h1>
          <p class="brand-subtitle">专业击剑赛事编排与计分系统</p>
        </div>
      </el-col>

      <el-col :md="12" class="right-actions">
        <div class="action-cards">
          <div class="entry-card" @click="handleCreate">
            <div class="icon-box plus">
              <el-icon>
                <Plus/>
              </el-icon>
            </div>
            <div class="text-box">
              <h3>创建赛事</h3>
              <p>开启一个新的击剑锦标赛或俱乐部比赛</p>
            </div>
          </div>

          <div class="entry-card" @click="handleGoToList">
            <div class="icon-box list">
              <el-icon>
                <List/>
              </el-icon>
            </div>
            <div class="text-box">
              <h3>已有赛事</h3>
              <p>查看并管理正在进行中或已结束的历史赛事</p>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import {ref} from 'vue'
import {useRouter} from 'vue-router'
import {Sunny, Moon, Plus, List, Odometer, ArrowDown} from '@element-plus/icons-vue'
import {useDark, useToggle} from '@vueuse/core'

const router = useRouter()
const isLoggedIn = ref(false)

// 主题切换逻辑 (需安装 @vueuse/core)
const isDark = useDark()
const toggleDark = useToggle(isDark)

const handleCreate = () => {
  // 逻辑：弹出创建窗口或跳转
  router.push('/tournament/create')
}

const handleGoToList = () => {
  // 跳转到赛事列表（你可以复用之前的 Dashboard 或列表逻辑）
  router.push('/tournament')
}
</script>

<style scoped lang="scss">
.home-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--el-bg-color-page);
  transition: all 0.3s ease;
}

.top-toolbar {
  position: absolute;
  top: 20px;
  right: 40px;
  display: flex;
  align-items: center;
  z-index: 10;
}

.hero-section {
  flex: 1;
  display: flex;
  align-items: center;
}

.left-brand {
  display: flex;
  justify-content: center;
  align-items: center;
  text-align: center;
  border-right: 1px solid var(--el-border-color-lighter);

  .brand-title {
    font-size: 4rem;
    margin: 10px 0;
    background: linear-gradient(45deg, #409eff, #67c23a);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .brand-subtitle {
    font-size: 1.2rem;
    color: var(--el-text-color-secondary);
  }
}

.right-actions {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 0 60px;
}

.action-cards {
  width: 100%;
  max-width: 450px;
}

.entry-card {
  display: flex;
  align-items: center;
  padding: 24px;
  margin-bottom: 20px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
    border-color: #409eff;
  }

  .icon-box {
    width: 56px;
    height: 56px;
    border-radius: 10px;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 24px;
    margin-right: 20px;

    &.plus {
      background-color: rgba(64, 158, 255, 0.1);
      color: #409eff;
    }

    &.list {
      background-color: rgba(103, 194, 58, 0.1);
      color: #67c23a;
    }
  }

  h3 {
    margin: 0 0 4px 0;
    font-size: 1.2rem;
  }

  p {
    margin: 0;
    font-size: 0.9rem;
    color: #909399;
  }
}

/* 移动端适配 */
@media (max-width: 768px) {
  .hero-section {
    flex-direction: column;
  }
  .left-brand {
    border-right: none;
    border-bottom: 1px solid var(--el-border-color-lighter);
    padding: 60px 0;
  }
  .right-actions {
    padding: 40px 20px;
  }
}
</style>