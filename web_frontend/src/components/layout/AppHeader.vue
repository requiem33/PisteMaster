<template>
  <header class="list-header">
    <div class="logo-section" @click="router.push('/')">
      <el-icon :size="28" class="logo-icon">
        <Trophy/>
      </el-icon>
      <span class="app-name">PisteMaster</span>
      <el-divider direction="vertical"/>
      <span class="page-title">{{ title }}</span>
      <slot name="extra"></slot>
    </div>

    <div class="actions-section">
      <el-dropdown @command="handleLanguageCommand" trigger="click" class="tool-item">
        <el-button circle>
          <span class="lang-text">{{ locale === 'zh-CN' ? '中' : 'EN' }}</span>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="zh-CN" :disabled="locale === 'zh-CN'">简体中文</el-dropdown-item>
            <el-dropdown-item command="en-US" :disabled="locale === 'en-US'">English</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <el-tooltip :content="isDark ? '切换到白天模式' : '切换到夜晚模式'" placement="bottom">
        <el-button
            class="tool-item"
            :icon="isDark ? Sunny : Moon"
            circle
            @click="toggleDark()"
        />
      </el-tooltip>

      <el-divider direction="vertical"/>

      <div class="user-slot">
        <slot name="user"></slot>
        <el-button v-if="showCreate" type="primary" :icon="Plus" @click="$emit('create')">
          {{ $t('common.actions.create') }}
        </el-button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import {useRouter} from 'vue-router'
import {useDark, useToggle} from '@vueuse/core'
import {useI18n} from 'vue-i18n'
import {Trophy, Sunny, Moon, Plus} from '@element-plus/icons-vue'

// 定义属性
interface Props {
  title: string
  showCreate?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showCreate: false
})

// 定义事件
defineEmits(['create'])

const router = useRouter()

/* --- 国际化逻辑 --- */
const {locale} = useI18n()

const handleLanguageCommand = (lang: string) => {
  locale.value = lang
  localStorage.setItem('lang', lang) // 持久化存储用户选择
}

/* --- 暗黑模式逻辑 --- */
const isDark = useDark({
  selector: 'html',
  attribute: 'class',
  valueDark: 'dark',
  valueLight: '',
})
const toggleDark = useToggle(isDark)
</script>

<style scoped lang="scss">
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 60px;
  background-color: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
  /* 毛玻璃效果 */
  backdrop-filter: blur(10px);
  position: sticky;
  top: 0;
  z-index: 1000;

  .logo-section {
    display: flex;
    align-items: center;
    gap: 12px;
    cursor: pointer;

    .logo-icon {
      color: var(--el-color-primary);
    }

    .app-name {
      font-weight: bold;
      font-size: 18px;
      letter-spacing: 0.5px;
      background: linear-gradient(90deg, var(--el-color-primary), #36cfc9);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .page-title {
      font-size: 15px;
      color: var(--el-text-color-regular);
    }
  }

  .actions-section {
    display: flex;
    align-items: center;
    gap: 12px;

    .tool-item {
      margin-right: 4px;
    }

    .lang-text {
      font-size: 12px;
      font-weight: bold;
      color: var(--el-color-primary);
    }

    .user-slot {
      display: flex;
      align-items: center;
      gap: 12px;
    }
  }
}

/* 兼容深色模式的平滑过渡 */
:deep(.el-button) {
  transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
}
</style>