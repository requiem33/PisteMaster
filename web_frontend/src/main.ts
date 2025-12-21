import {createApp} from 'vue'
import {createPinia} from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import i18n from './locales' // 引入国际化配置

import './styles/theme.scss'

import App from './App.vue'
import router from './router' // 👈 引入路由配置

const app = createApp(App)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
}

app.use(createPinia())
app.use(router)       // 👈 必须在 mount 之前使用
app.use(ElementPlus)
app.use(i18n)         // 使用国际化配置
app.mount('#app')