<template>
  <div class="home-container">
    <AppHeader :showCreate="false">
      <template #user>
        <div class="header-user-area">
          <el-button v-if="!isLoggedIn" type="primary" link @click="isLoggedIn = true">注册 / 登录</el-button>
          <el-dropdown v-else>
            <span class="user-info">
              <el-avatar :size="24" src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png"/>
              <span class="username">管理员</span>
              <el-icon><ArrowDown/></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>个人中心</el-dropdown-item>
                <el-dropdown-item divided @click="isLoggedIn = false">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-divider direction="vertical"/>
        </div>
      </template>
    </AppHeader>

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
              <h3>赛事列表</h3>
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
import {Plus, List, Odometer, ArrowDown} from '@element-plus/icons-vue'
import AppHeader from '@/components/layout/AppHeader.vue'

const router = useRouter()
const isLoggedIn = ref(false)

const handleCreate = () => router.push('/tournament/create')
const handleGoToList = () => router.push('/tournament')
</script>

<style scoped lang="scss">
.home-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--el-bg-color-page);
}

.header-user-area {
  display: flex;
  align-items: center;

  .user-info {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    font-size: 14px;
    color: var(--el-text-color-primary);

    .username {
      font-weight: 500;
    }
  }
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
  height: 60%; /* 限制高度使分割线不贯穿全屏 */

  .brand-title {
    font-size: 4rem;
    margin: 10px 0;
    background: linear-gradient(45deg, #409eff, #67c23a);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
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
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);

  &:hover {
    transform: translateX(10px); /* 首页特有的横向位移动效 */
    box-shadow: var(--el-box-shadow-light);
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
    color: var(--el-text-color-secondary);
  }
}

@media (max-width: 768px) {
  .hero-section {
    flex-direction: column;
  }
  .left-brand {
    border-right: none;
    border-bottom: 1px solid var(--el-border-color-lighter);
    width: 100%;
    padding: 40px 0;
  }
  .right-actions {
    padding: 40px 20px;
    width: 100%;
  }
}
</style>