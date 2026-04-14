<template>
  <el-config-provider :locale="currentLocale">
    <router-view/>
  </el-config-provider>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import enUs from 'element-plus/es/locale/lang/en'
import i18n from './locales'
import router from './router'
import { useSyncStore } from '@/stores/syncStore'
import { isElectron } from '@/utils/platform'

const syncStore = useSyncStore()

// 根据i18n的当前语言动态切换Element Plus的语言
const currentLocale = computed(() => {
  return i18n.global.locale.value === 'zh-CN' ? zhCn : enUs
})

// 添加路由守卫处理国际化标题
router.beforeEach((to, _from, next) => {
  if (to.meta.titleKey) {
    // 使用i18n翻译页面标题
    document.title = i18n.global.t(to.meta.titleKey as string)
  }
  next()
})

// Initialize sync store on app startup for Electron desktop mode
onMounted(() => {
  if (isElectron()) {
    console.log('[App] Initializing sync store for Electron desktop')
    syncStore.initialize().catch((error) => {
      console.error('[App] Failed to initialize sync store:', error)
    })
  }
})
</script>