<template>
  <div class="user-menu">
    <template v-if="authStore.isAuthenticated">
      <span class="username">{{ authStore.username }}</span>
      <el-tag v-if="authStore.isAdmin" type="danger" size="small">Admin</el-tag>
      <el-tag v-else-if="authStore.isScheduler" type="success" size="small">Scheduler</el-tag>
      <el-tag v-else-if="authStore.isGuest" type="info" size="small">{{ t('auth.guest') }}</el-tag>
      <el-divider direction="vertical" />
      <el-button v-if="showSettings" link @click="router.push('/settings')">
        <el-icon><Setting /></el-icon>
        {{ t('cluster.settings') }}
      </el-button>
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
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { Setting } from '@element-plus/icons-vue'
import { isElectron } from '@/utils/platform'

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()

const showSettings = computed(() => {
  if (!isElectron()) {
    return false
  }
  return authStore.isAdmin || authStore.isScheduler
})

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