<template>
  <div class="tournament-list-page">
    <AppHeader :title="$t('tournament.listTitle')" :showCreate="false"/>

    <main class="content">
      <div class="filter-bar">
        <el-input
            v-model="searchQuery"
            :placeholder="$t('common.search') + '...'"
            prefix-icon="Search"
            clearable
            style="width: 300px"
        />
        <el-radio-group v-model="statusFilter" class="ml-20">
          <el-radio-button label="all">{{ $t('common.all') }}</el-radio-button>
          <el-radio-button label="ongoing">{{ $t('common.ongoing') }}</el-radio-button>
          <el-radio-button label="completed">{{ $t('common.completed') }}</el-radio-button>
        </el-radio-group>
      </div>

      <el-row :gutter="20" class="tournament-grid">
        <el-col
            v-for="item in filteredTournaments"
            :key="item.id"
            :xs="24" :sm="12" :md="8" :lg="6"
        >
          <el-card shadow="hover" class="event-card" @click="goToOrchestrator(item.id)">
            <div class="card-status">
              <el-tag :type="item.status === 'completed' ? 'info' : 'success'" size="small">
                {{ item.status === 'completed' ? $t('common.completed') : $t('common.ongoing') }}
              </el-tag>
            </div>

            <h3 class="event-name">{{ item.name }}</h3>

            <div class="meta-info">
              <p class="event-meta">
                <el-icon>
                  <Calendar/>
                </el-icon>
                {{ item.date }}
              </p>
              <p class="event-meta">
                <el-icon>
                  <User/>
                </el-icon>
                {{ $t('common.fencerCount') }}: {{ item.fencerCount }}
              </p>
            </div>

            <template #footer>
              <div class="card-footer">
                <span class="rule-type">{{ item.rule }}</span>
                <el-button link type="primary">{{ $t('common.enterOrchestration') }}
                  <el-icon>
                    <ArrowRight/>
                  </el-icon>
                </el-button>
              </div>
            </template>
          </el-card>
        </el-col>
      </el-row>

      <el-empty v-if="filteredTournaments.length === 0" :description="$t('common.noMatch')"/>
    </main>
  </div>
</template>

<script setup lang="ts">
import {ref, computed} from 'vue'
import {useRouter} from 'vue-router'
import {useDark, useToggle} from '@vueuse/core'
import {
  Trophy, Plus, Moon, Sunny, Search,
  Calendar, User, ArrowRight
} from '@element-plus/icons-vue'
import AppHeader from '@/components/layout/AppHeader.vue'

const router = useRouter()

// --- 主题切换逻辑 ---
const isDark = useDark()
const toggleDark = useToggle(isDark)

// --- 搜索与过滤 ---
const searchQuery = ref('')
const statusFilter = ref('all')

const tournaments = ref([
  {
    id: 'e1',
    name: '2024 全国击剑俱乐部联赛 (上海站)',
    date: '2024-10-20',
    status: 'ongoing',
    fencerCount: 128,
    rule: 'FIE 标准'
  },
  {id: 'e2', name: '公开赛 - 男子重剑个人', date: '2024-11-05', status: 'ongoing', fencerCount: 64, rule: 'FIE 标准'},
  {id: 'e3', name: '高校击剑邀请赛', date: '2023-12-15', status: 'completed', fencerCount: 45, rule: '简易规则'},
])

const filteredTournaments = computed(() => {
  return tournaments.value.filter(t => {
    const matchesSearch = t.name.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchesStatus = statusFilter.value === 'all' || t.status === statusFilter.value
    return matchesSearch && matchesStatus
  })
})

const createNewEvent = () => {
  router.push('/tournament/create')
}

const goToOrchestrator = (id: string) => {
  router.push(`/tournament/${id}`)
}
</script>

<style scoped lang="scss">
.tournament-list-page {
  min-height: 100vh;
  background-color: var(--el-bg-color-page);
}

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
  z-index: 100;

  .logo-section {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    transition: opacity 0.2s;

    &:hover {
      opacity: 0.8;
    }

    .app-name {
      font-size: 18px;
      font-weight: bold;
      letter-spacing: -0.5px;
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

.content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 30px 40px;

  .filter-bar {
    margin-bottom: 30px;
    display: flex;
    align-items: center;
  }

  .ml-20 {
    margin-left: 20px;
  }
}

.event-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  margin-bottom: 20px;
  border: 1px solid var(--el-border-color-lighter);

  &:hover {
    transform: translateY(-4px);
    box-shadow: var(--el-box-shadow-light);
    border-color: var(--el-color-primary-light-5);
  }

  .event-name {
    margin: 10px 0;
    font-size: 16px;
    line-height: 1.5;
    font-weight: 600;
    min-height: 48px;
  }

  .meta-info {
    margin-bottom: 15px;
  }

  .event-meta {
    font-size: 13px;
    color: var(--el-text-color-secondary);
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 4px 0;
  }

  .card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .rule-type {
      font-size: 12px;
      color: var(--el-text-color-placeholder);
    }
  }
}
</style>