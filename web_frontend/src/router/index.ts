import {createRouter, createWebHashHistory} from 'vue-router'

// 导入你的视图组件
// 注意：确保你的文件名和路径完全匹配
const router = createRouter({
    history: createWebHashHistory(),
    routes: [
        {
            path: '/',
            name: 'index',
            component: () => import('../views/index.vue'),
            meta: {titleKey: 'common.pageTitles.index'}
        },
        {
            path: '/tournament',
            name: 'TournamentList',
            component: () => import('../views/TournamentList.vue'),
            meta: {titleKey: 'common.pageTitles.tournamentList'}
        },
        {
            path: '/tournament/create',
            name: 'TournamentCreate',
            component: () => import('../views/TournamentCreate.vue'), // 👈 新建这个组件
            meta: {titleKey: 'common.pageTitles.tournamentCreate'}
        },
        {
            path: '/tournament/:id',
            name: 'TournamentDashboard',
            component: () => import('../views/TournamentDashboard.vue'),
            meta: {titleKey: 'common.pageTitles.tournamentDashboard'}
        },
        {
            path: '/event/:id',
            name: 'EventOrchestrator',
            component: () => import('../views/EventOrchestrator.vue'),
            meta: {titleKey: 'common.pageTitles.eventOrchestrator'}
        }
    ]
})

export default router