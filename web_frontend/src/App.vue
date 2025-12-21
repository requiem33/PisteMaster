<template>
  <el-config-provider :locale="currentLocale">
    <router-view/>
  </el-config-provider>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import enUs from 'element-plus/es/locale/lang/en'
import i18n from './locales'
import router from './router'

// 根据i18n的当前语言动态切换Element Plus的语言
const currentLocale = computed(() => {
  return i18n.global.locale.value === 'zh-CN' ? zhCn : enUs
})

// 添加路由守卫处理国际化标题
router.beforeEach((to, from, next) => {
  if (to.meta.titleKey) {
    // 使用i18n翻译页面标题
    document.title = i18n.global.t(to.meta.titleKey as string)
  }
  next()
})
</script>