<template>
  <header class="list-header">
    <div class="logo-section" @click="router.push('/')" title="返回首页">
      <el-icon size="24" color="#409EFF">
        <Trophy/>
      </el-icon>
      <span class="app-name">PisteMaster</span>
      <el-divider direction="vertical"/>
      <span class="page-title">{{ title }}</span>
    </div>

    <div class="actions">
      <el-button link @click="router.push('/')">首页</el-button>

      <el-tooltip :content="isDark ? '切换到白天模式' : '切换到夜晚模式'" placement="bottom">
        <el-button
            :icon="isDark ? 'Sunny' : 'Moon'"
            circle
            @click="toggleDark()"
            class="theme-toggle"
        />
      </el-tooltip>

      <el-divider direction="vertical"/>

      <slot name="extra"></slot>

      <el-button v-if="showCreate" type="primary" icon="Plus" @click="router.push('/create-event')">
        新建赛事
      </el-button>
    </div>
  </header>
</template>

<script setup lang="ts">
import {useRouter} from 'vue-router'
import {useDark, useToggle} from '@vueuse/core'
import {Trophy, Sunny, Moon, Plus} from '@element-plus/icons-vue'

defineProps<{
  title: string,
  showCreate?: boolean
}>()

const router = useRouter()
const isDark = useDark()
const toggleDark = useToggle(isDark)
</script>

<style scoped lang="scss">
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
  height: 64px;
  background-color: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
  position: sticky;
  top: 0;
  z-index: 1000;

  .logo-section {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;

    .app-name {
      font-weight: bold;
      font-size: 18px;
    }

    .page-title {
      font-size: 14px;
      color: var(--el-text-color-secondary);
    }
  }

  .actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}
</style>