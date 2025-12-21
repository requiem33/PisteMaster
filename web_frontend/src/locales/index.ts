import {createI18n} from 'vue-i18n'
import zhCN from './zh-CN' // 自动指向 zh-CN/index.ts
import enUS from './en-US' // 自动指向 en-US/index.ts

const i18n = createI18n({
    legacy: false,
    locale: localStorage.getItem('lang') || 'zh-CN',
    fallbackLocale: 'en-US',
    messages: {
        'zh-CN': zhCN,
        'en-US': enUS,
    }
})

export default i18n