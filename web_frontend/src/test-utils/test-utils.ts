/**
 * Test utilities for Vue component testing
 * Provides helper functions and Vue Test Utils configurations
 */

import { type Component } from 'vue'
import { type Router } from 'vue-router'
import { render, type RenderOptions } from '@vue/test-utils'
import { createPinia, type Pinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

export interface TestRenderOptions extends RenderOptions {
  pinia?: Pinia
  router?: Router
  initialState?: Record<string, unknown>
}

export function createTestPinia(initialState?: Record<string, unknown>): Pinia {
  const pinia = createPinia()

  if (initialState) {
    pinia.state.value = initialState
  }

  return pinia
}

export function createTestRouter(routes: Array<{ path: string; component: Component }> = []): Router {
  return createRouter({
    history: createWebHistory(),
    routes:
      routes.length > 0 ? routes : [{ path: '/', component: { template: '<div />' } }],
  })
}

export function renderComponent(
  component: Component,
  options: TestRenderOptions = {}
) {
  const {
    pinia = createTestPinia(options.initialState),
    router = createTestRouter(),
    global: globalOptions = {},
    ...renderOptions
  } = options

  return render(component, {
    global: {
      plugins: [
        [pinia],
        [router],
        [ElementPlus],
      ],
      ...globalOptions,
    },
    ...renderOptions,
  })
}

export function getComponent<T>(
  wrapper: { findComponent: (selector: string) => { vm: T } },
  selector: string
): T | null {
  return wrapper.findComponent(selector)?.vm ?? null
}

export function waitFor(condition: () => boolean, timeout = 3000): Promise<void> {
  return new Promise((resolve, reject) => {
    const startTime = Date.now()
    
    const interval = setInterval(() => {
      if (condition()) {
        clearInterval(interval)
        resolve()
      } else if (Date.now() - startTime > timeout) {
        clearInterval(interval)
        reject(new Error('Wait timeout'))
      }
    }, 50)
  })
}

export function mockLocalStorage() {
  const store: Record<string, string> = {}
  
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      Object.keys(store).forEach(key => delete store[key])
    }),
    get length() {
      return Object.keys(store).length
    },
    key: vi.fn((index: number) => Object.keys(store)[index] || null),
  }
}

export function mockSessionStorage() {
  return mockLocalStorage()
}

export const flushPromises = () => new Promise(resolve => setTimeout(resolve, 0))

declare module 'vitest' {
  interface AsymmetricMatchers {
    toBeValidUUID(): any
  }
}

expect.extend({
  toBeValidUUID(received: string) {
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
    const pass = uuidRegex.test(received)
    
    return {
      pass,
      message: () =>
        pass
          ? `expected ${received} not to be a valid UUID`
          : `expected ${received} to be a valid UUID`,
    }
  },
})