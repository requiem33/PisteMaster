<template>
  <div class="dashboard-container">
    <AppHeader :title="$t('tournament.dashboard.title')" :showCreate="false">
      <template #extra>
        <el-breadcrumb separator-class="el-icon-arrow-right" class="header-breadcrumb">
          <el-breadcrumb-item :to="{ path: '/' }">{{ $t('tournament.dashboard.breadcrumb.home') }}</el-breadcrumb-item>
          <el-breadcrumb-item :to="{ path: '/tournament' }">{{
              $t('tournament.dashboard.breadcrumb.tournamentList')
            }}
          </el-breadcrumb-item>
          <el-breadcrumb-item>{{ $t('tournament.dashboard.breadcrumb.currentTournament') }}</el-breadcrumb-item>
        </el-breadcrumb>
      </template>

      <template #user>
        <div class="header-user-area">
          <el-dropdown>
            <span class="user-info">
              <el-avatar :size="24" src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png"/>
              <span class="username">管理员</span>
              <el-icon><ArrowDown/></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item icon="User">{{ $t('common.userCenter') }}</el-dropdown-item>
                <el-dropdown-item divided icon="SwitchButton">{{ $t('common.logout') }}</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-divider direction="vertical"/>
        </div>
      </template>
    </AppHeader>

    <div class="dashboard-content">
      <header class="tournament-info-banner">
        <div class="title-bar">
          <div class="tournament-main-info">
            <div class="title-with-tag">
              <h1>{{ tournamentInfo.tournament_name }}</h1>
              <el-tag effect="dark" type="primary">{{ $t('tournament.dashboard.tournamentStatus') }}</el-tag>
            </div>
            <div class="meta-tags">
              <span class="meta-item"><el-icon><Location/></el-icon> {{ tournamentInfo.location }}</span>
              <span class="meta-item">
                <el-icon><Calendar/></el-icon>
                {{ tournamentInfo.start_date }} 至 {{ tournamentInfo.end_date }}
              </span>
            </div>
          </div>
          <div class="header-actions">
            <el-button icon="Edit">{{ $t('tournament.dashboard.editInfo') }}</el-button>
            <el-button type="primary" icon="Plus" @click="eventDrawerVisible = true">
              {{ $t('tournament.dashboard.addEvent') }}
            </el-button>
          </div>
        </div>
      </header>

      <el-row :gutter="20" class="stat-row">
        <el-col :span="6">
          <el-card shadow="never" class="stat-card">
            <div class="label">{{ $t('tournament.dashboard.stats.totalEvents') }}</div>
            <div class="value">{{ events.length }}</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never" class="stat-card">
            <div class="label">{{ $t('tournament.dashboard.stats.totalFencers') }}</div>
            <div class="value">{{ totalFencersCount }}</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never" class="stat-card">
            <div class="label">{{ $t('tournament.dashboard.stats.activePistes') }}</div>
            <div class="value">12</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never" class="stat-card highlight">
            <div class="label">{{ $t('tournament.dashboard.stats.syncStatus') }}</div>
            <div class="value">
              <el-icon>
                <Cloudy/>
              </el-icon>
              {{ $t('tournament.dashboard.stats.realtime') }}
            </div>
          </el-card>
        </el-col>
      </el-row>

      <section class="events-grid">
        <div class="section-title">
          <h2>{{ $t('tournament.dashboard.eventSection') }} (Events)</h2>
          <el-radio-group v-model="filterType" size="small">
            <el-radio-button label="all">{{ $t('tournament.dashboard.filterAll') }}</el-radio-button>
            <el-radio-button label="individual">{{ $t('tournament.dashboard.filterIndividual') }}</el-radio-button>
            <el-radio-button label="team">{{ $t('tournament.dashboard.filterTeam') }}</el-radio-button>
          </el-radio-group>
        </div>

        <el-empty v-if="events.length === 0" :description="$t('tournament.dashboard.noEvents')"/>

        <el-row :gutter="20" v-else>
          <el-col :md="8" :sm="12" :xs="24" v-for="event in events" :key="event.id">
            <el-card class="event-card" shadow="hover">
              <div class="event-card-body">
                <div class="event-type-icon">
                  <el-icon :size="24">
                    <Trophy/>
                  </el-icon>
                </div>
                <div class="event-details">
                  <h3>{{ event.event_name }}</h3>
                  <p class="rule-text">{{ event.rule_name }}</p>
                  <div class="event-tags">
                    <el-tag size="small" type="info">{{ event.is_team_event ? '团体赛' : '个人赛' }}</el-tag>
                    <el-tag size="small" :type="getStatusType(event.status)">{{ event.status }}</el-tag>
                  </div>
                </div>
              </div>
              <div class="event-card-footer">
                <div class="fencer-count">
                  <el-icon>
                    <User/>
                  </el-icon>
                  <span>{{ event.fencer_count }}</span>
                </div>
                <el-button type="primary" link @click="goToOrchestrator(event.id)">
                  <el-icon>
                    <Right/>
                  </el-icon>
                </el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </section>
    </div>

    <CreateEventDrawer
        v-model="eventDrawerVisible"
        :tournamentId="tournamentId"
        @success="handleEventCreated"
    />
  </div>
</template>

<script setup lang="ts">
import {onMounted, ref, computed} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {Location, Calendar, Cloudy, Trophy, User, Right, Plus, Edit, ArrowDown} from '@element-plus/icons-vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import CreateEventDrawer from '@/components/tournament/CreateEventDrawer.vue'
import {DataManager} from '@/services/DataManager'
import {ElMessage} from "element-plus";

const route = useRoute()
const router = useRouter()
const tournamentId = route.params.id as string

const loading = ref(false)
const eventDrawerVisible = ref(false)
const filterType = ref('all')

// 初始值设为空，等待加载
const tournamentInfo = ref<any>({
  tournament_name: '',
  location: '',
  start_date: '',
  end_date: ''
})

const events = ref<any[]>([])

// 计算总参赛人数 (所有项目的人数总和)
const totalFencersCount = computed(() => {
  return events.value.reduce((sum, event) => {
    return sum + (Number(event.fencer_count) || 0)
  }, 0)
})

// --- 加载数据函数 ---
const loadAllData = async () => {
  loading.value = true
  try {
    // 并行获取赛事信息和下属项目
    const [info, eventList] = await Promise.all([
      DataManager.getTournamentById(tournamentId),
      DataManager.getEventsByTournamentId(tournamentId)
    ])

    if (info) {
      tournamentInfo.value = info
    } else {
      ElMessage.error('未找到赛事信息')
      router.push('/tournament')
    }

    events.value = eventList
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadAllData()
})

const getStatusType = (status: string) => {
  const types: Record<string, string> = {'正在报名': 'success', '编排中': 'warning', '已结束': 'info'}
  return types[status] || ''
}

const handleEventCreated = () => {
  loadAllData() // 项目创建成功后刷新列表
  eventDrawerVisible.value = false
}

const goToOrchestrator = (eventId: string) => router.push(`/event/${eventId}`)
</script>

<style scoped lang="scss">
.dashboard-container {
  min-height: 100vh;
  background-color: var(--el-bg-color-page);
}

.dashboard-content {
  padding: 30px 40px;
  max-width: 1400px;
  margin: 0 auto;
}

.header-breadcrumb {
  margin-left: 10px;
  font-size: 13px;
}

.header-user-area {
  display: flex;
  align-items: center;

  .user-info {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    font-size: 14px;
    color: var(--el-text-color-primary);
  }
}

.tournament-info-banner {
  margin-bottom: 30px;

  .title-bar {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;

    .title-with-tag {
      display: flex;
      align-items: center;
      gap: 15px;
      margin-bottom: 10px;

      h1 {
        margin: 0;
        font-size: 28px;
        font-weight: 700;
      }
    }

    .meta-tags {
      display: flex;
      gap: 20px;
      color: var(--el-text-color-secondary);
      font-size: 14px;

      .meta-item {
        display: flex;
        align-items: center;
        gap: 4px;
      }
    }
  }
}

.stat-row {
  margin-bottom: 40px;

  .stat-card {
    border-radius: 12px;
    border: none;
    background-color: var(--el-bg-color);

    .label {
      color: var(--el-text-color-secondary);
      font-size: 14px;
    }

    .value {
      font-size: 26px;
      font-weight: bold;
      margin-top: 8px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    &.highlight {
      border-top: 4px solid var(--el-color-primary);
    }
  }
}

.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  h2 {
    margin: 0;
    font-size: 20px;
  }
}

.event-card {
  margin-bottom: 20px;
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);

  .event-card-body {
    display: flex;
    gap: 15px;
    margin-bottom: 20px;

    .event-type-icon {
      width: 48px;
      height: 48px;
      background: var(--el-color-primary-light-9);
      color: var(--el-color-primary);
      border-radius: 8px;
      display: flex;
      justify-content: center;
      align-items: center;
    }

    .event-details {
      h3 {
        margin: 0 0 5px 0;
        font-size: 16px;
      }

      .rule-text {
        font-size: 12px;
        color: var(--el-text-color-secondary);
        margin: 0 0 10px 0;
      }

      .event-tags {
        display: flex;
        gap: 8px;
      }
    }
  }

  .event-card-footer {
    border-top: 1px solid var(--el-border-color-lighter);
    padding-top: 15px;
    display: flex;
    justify-content: space-between;
    align-items: center;

    .fencer-count {
      font-size: 13px;
      color: var(--el-text-color-regular);
      display: flex;
      align-items: center;
      gap: 5px;
    }
  }
}
</style>