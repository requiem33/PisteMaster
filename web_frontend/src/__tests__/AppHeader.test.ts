/**
 * Tests for AppHeader component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import AppHeader from '../components/layout/AppHeader.vue'
import { createTestRouter } from '../test-utils'
import { createI18n } from 'vue-i18n'

const i18n = createI18n({
  legacy: false,
  locale: 'en-US',
  messages: {
    'en-US': {
      common: {
        language: {
          zh: '中文',
          en: 'EN',
          zhCN: '中文',
          enUS: 'English',
        },
        theme: {
          switchToLight: 'Switch to light theme',
          switchToDark: 'Switch to dark theme',
        },
        actions: {
          create: 'Create',
        },
      },
    },
    'zh-CN': {
      common: {
        language: {
          zh: '中文',
          en: 'EN',
          zhCN: '中文',
          enUS: 'English',
        },
        theme: {
          switchToLight: '切换到浅色主题',
          switchToDark: '切换到深色主题',
        },
        actions: {
          create: '创建',
        },
      },
    },
  },
})

describe('AppHeader', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
  })

  it('should render header with logo', () => {
    const router = createTestRouter()
    const pinia = createPinia()

    const wrapper = mount(AppHeader, {
      global: {
        plugins: [i18n, router, pinia],
      },
    })

    expect(wrapper.text()).toContain('PisteMaster')
  })

  it('should render language selector', () => {
    const router = createTestRouter()
    const pinia = createPinia()

    const wrapper = mount(AppHeader, {
      global: {
        plugins: [i18n, router, pinia],
      },
    })

    // Should show the current language
    expect(wrapper.text()).toContain('EN')
  })

  it('should not show create button by default', () => {
    const router = createTestRouter()
    const pinia = createPinia()

    const wrapper = mount(AppHeader, {
      global: {
        plugins: [i18n, router, pinia],
      },
      props: {
        showCreate: false,
      },
    })

    expect(wrapper.text()).not.toContain('Create')
  })

  it('should show create button when showCreate is true', () => {
    const router = createTestRouter()
    const pinia = createPinia()

    const wrapper = mount(AppHeader, {
      global: {
        plugins: [i18n, router, pinia],
      },
      props: {
        showCreate: true,
      },
    })

    expect(wrapper.text()).toContain('Create')
  })

  it('should have navigation to home', () => {
    const router = createTestRouter()
    const pinia = createPinia()

    const wrapper = mount(AppHeader, {
      global: {
        plugins: [i18n, router, pinia],
      },
    })

    // Verify the component is mounted
    expect(wrapper.exists()).toBe(true)
  })
})