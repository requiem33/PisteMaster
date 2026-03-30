<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2>{{ t('auth.login') }}</h2>
      <el-form @submit.prevent="handleLogin">
        <el-form-item>
          <el-input
            v-model="username"
            :placeholder="t('auth.username')"
            :prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="password"
            type="password"
            :placeholder="t('auth.password')"
            :prefix-icon="Lock"
            show-password
            size="large"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-button
          type="primary"
          @click="handleLogin"
          :loading="loading"
          size="large"
          style="width: 100%"
        >
          {{ t('auth.login') }}
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { User, Lock } from '@element-plus/icons-vue'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const loading = ref(false)

const handleLogin = async () => {
  if (!username.value || !password.value) {
    ElMessage.warning(t('auth.enterCredentials'))
    return
  }

  loading.value = true
  const success = await authStore.login(username.value, password.value)

  if (success) {
    ElMessage.success(t('auth.loginSuccess'))
    const redirect = route.query.redirect as string
    router.push(redirect || '/')
  } else {
    ElMessage.error(t('auth.loginFailed'))
  }

  loading.value = false
}
</script>

<style scoped lang="scss">
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 120px);
  padding: 24px;

  .login-card {
    width: 100%;
    max-width: 400px;

    h2 {
      text-align: center;
      margin-bottom: 24px;
      color: var(--el-text-color-primary);
    }
  }
}
</style>