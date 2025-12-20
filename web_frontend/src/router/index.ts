import {createRouter, createWebHistory} from 'vue-router'

// 导入你的视图组件
// 注意：确保你的文件名和路径完全匹配
const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/',
            name: 'index',
            component: () => import('../views/index.vue')
        },
        {
            path: '/tournament',
            name: 'TournamentList',
            component: () => import('../views/TournamentList.vue')
        },
        {
            path: '/tournament/:id',
            name: 'TournamentDashboard',
            component: () => import('../views/TournamentDashboard.vue')
        },
        {
            path: '/event/:id',
            name: 'EventOrchestrator',
            component: () => import('../views/EventOrchestrator.vue')
        }
    ]
})

export default router