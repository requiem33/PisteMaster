<template>
  <header class="list-header">
    <div class="logo-section">
      <div class="home-link" @click="router.push('/')">
        <el-icon :size="28" class="logo-icon">
          <Trophy/>
        </el-icon>
        <span class="app-name">PisteMaster</span>
      </div>
      <el-divider direction="vertical"/>

      <!-- 移除 title, 让 slot 里的面包屑直接跟在后面 -->
      <slot name="extra"></slot>
    </div>

    <div class="actions-section">
      <!-- ... (右侧操作区保持不变) ... -->
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
// --- <script> 部分完全保持不变 ---
import {useRouter} from 'vue-router'
import {useDark, useToggle} from '@vueuse/core'
import {useI18n} from 'vue-i18n'
import {Trophy, Sunny, Moon, Plus} from '@element-plus/icons-vue'

interface Props {
  showCreate?: boolean
}

withDefaults(defineProps<Props>(), {showCreate: false})
defineEmits(['create'])
const router = useRouter()
const {locale} = useI18n()
const handleLanguageCommand = (lang: string) => {
  locale.value = lang
  localStorage.setItem('lang', lang)
}
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
  backdrop-filter: blur(10px);
  position: sticky;
  top: 0;
  z-index: 1000;

  .logo-section {
    display: flex;
    align-items: center;
    gap: 12px;
    // 移除父元素的 cursor: pointer
  }

  // 【关键修复】2. 为新的 home-link 容器添加样式
  .home-link {
    display: flex;
    align-items: center;
    gap: 12px;
    cursor: pointer; // 只让这部分可点击

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
  }

  .page-title {
    font-size: 15px;
    color: var(--el-text-color-regular);
  }

  .actions-section {
    // ... (右侧样式保持不变) ...
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

:deep(.el-button) {
  transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
}
</style>
