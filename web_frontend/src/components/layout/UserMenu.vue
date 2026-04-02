<template>
  <div class="user-menu">
    <template v-if="authStore.isAuthenticated">
      <span class="username">{{ authStore.username }}</span>
      <el-tag v-if="authStore.isAdmin" type="danger" size="small">Admin</el-tag>
      <el-tag v-else-if="authStore.isScheduler" type="success" size="small">Scheduler</el-tag>
      <el-tag v-else-if="authStore.isGuest" type="info" size="small">{{ t('auth.guest') }}</el-tag>
      <el-button link @click="handleLogout">{{ t('auth.logout') }}</el-button>
    </template>
    <template v-else>
      <el-button type="primary" @click="router.push('/login')">
        {{ t('auth.login') }}
      </el-button>
    </template>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()

const handleLogout = async () => {
  await authStore.logout()
  ElMessage.success(t('auth.logoutSuccess'))
  router.push('/')
}
</script>

<style scoped lang="scss">
.user-menu {
  display: flex;
  align-items: center;
  gap: 12px;

  .username {
    font-weight: 500;
    color: var(--el-text-color-primary);
  }
}
</style>