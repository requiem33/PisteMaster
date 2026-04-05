import {createRouter, createWebHashHistory} from 'vue-router'
import {useAuthStore} from '@/stores/authStore'
import {isElectron} from '@/utils/platform'

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
            component: () => import('../views/TournamentCreate.vue'),
            meta: {titleKey: 'common.pageTitles.tournamentCreate', requiresAuth: true}
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
        },
        {
            path: '/settings',
            name: 'Settings',
            component: () => import('../views/Settings.vue'),
            meta: {titleKey: 'common.pageTitles.settings', requiresAuth: true, requiresAdminOrScheduler: true}
        },
        {
            path: '/login',
            name: 'Login',
            component: () => import('../views/Login.vue'),
            meta: {titleKey: 'auth.login'}
        }
    ]
})

router.beforeEach(async (to, _from, next) => {
    const authStore = useAuthStore()

    if (!authStore.user) {
        await authStore.fetchCurrentUser()
    }

    if (to.path === '/login' && authStore.isAuthenticated) {
        next('/')
        return
    }

    const requiresAuth = to.meta.requiresAuth as boolean
    if (requiresAuth && !authStore.isAuthenticated) {
        if (isElectron() && authStore.isGuest) {
            next()
            return
        }
        next({path: '/login', query: {redirect: to.fullPath}})
        return
    }

    const requiresAdminOrScheduler = to.meta.requiresAdminOrScheduler as boolean
    if (requiresAdminOrScheduler) {
        if (!authStore.isAdmin && !authStore.isScheduler) {
            next({path: '/'})
            return
        }
    }

    next()
})

export default router