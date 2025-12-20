<template>
  <div class="dashboard-container">
    <header class="dashboard-header">
      <el-breadcrumb separator-class="el-icon-arrow-right">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item>赛事控制台</el-breadcrumb-item>
      </el-breadcrumb>

      <div class="title-bar">
        <div class="tournament-main-info">
          <h1>{{ tournamentInfo.tournament_name }}</h1>
          <div class="meta-tags">
            <el-tag size="small" effect="dark" type="primary">进行中</el-tag>
            <span class="meta-item"><el-icon><Location/></el-icon> {{ tournamentInfo.location }}</span>
            <span class="meta-item"><el-icon><Calendar/></el-icon> {{
                tournamentInfo.start_date
              }} 至 {{ tournamentInfo.end_date }}</span>
          </div>
        </div>
        <div class="header-actions">
          <el-button icon="Edit">编辑赛事信息</el-button>
          <el-button type="primary" icon="Plus" @click="eventDrawerVisible = true">新增竞赛项目</el-button>
        </div>
      </div>
    </header>

    <el-row :gutter="20" class="stat-row">
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="label">项目总数</div>
          <div class="value">{{ events.length }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="label">已报名选手</div>
          <div class="value">128</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="label">当前活跃剑道</div>
          <div class="value">12</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card highlight">
          <div class="label">同步状态</div>
          <div class="value">
            <el-icon>
              <Cloudy/>
            </el-icon>
            实时
          </div>
        </el-card>
      </el-col>
    </el-row>

    <section class="events-grid">
      <div class="section-title">
        <h2>竞赛项目 (Events)</h2>
        <el-radio-group v-model="filterType" size="small">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="individual">个人赛</el-radio-button>
          <el-radio-button label="team">团体赛</el-radio-button>
        </el-radio-group>
      </div>

      <el-empty v-if="events.length === 0" description="暂无项目，点击右上角创建第一个单项"/>

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
                <span>{{ event.fencer_count }} 选手</span>
              </div>
              <el-button type="primary" link icon="Right" @click="goToOrchestrator(event.id)">
                进入编排
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </section>

    <CreateEventDrawer
        v-model="eventDrawerVisible"
        :tournamentId="tournamentId"
        @success="handleEventCreated"
    />
  </div>
</template>

<script setup lang="ts">
import {ref, onMounted} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {Location, Calendar, Cloudy, Trophy, User, Right, Plus, Edit} from '@element-plus/icons-vue'
import CreateEventDrawer from '@/components/tournament/CreateEventDrawer.vue'

const route = useRoute()
const router = useRouter()
const tournamentId = route.params.id as string

// 状态控制
const eventDrawerVisible = ref(false)
const filterType = ref('all')

// 模拟赛事基础数据 (实际应从 API 获取)
const tournamentInfo = ref({
  tournament_name: '2025年全国击剑冠军赛 (第一站)',
  organizer: '中国击剑协会',
  location: '上海静安体育中心',
  start_date: '2025-12-20',
  end_date: '2025-12-25'
})

// 模拟项目数据
const events = ref([
  {
    id: 'e1',
    event_name: '成年男子重剑个人',
    rule_name: '15剑/9分钟',
    is_team_event: false,
    fencer_count: 64,
    status: '正在报名'
  },
  {
    id: 'e2',
    event_name: '成年女子花剑个人',
    rule_name: '15剑/9分钟',
    is_team_event: false,
    fencer_count: 42,
    status: '已结束'
  }
])

const getStatusType = (status: string) => {
  switch (status) {
    case '正在报名':
      return 'success'
    case '编排中':
      return 'warning'
    case '已结束':
      return 'info'
    default:
      return ''
  }
}

const handleEventCreated = () => {
  // 这里可以重新调用获取列表的接口
  console.log('项目已创建，刷新列表')
}

const goToOrchestrator = (eventId: string) => {
  router.push(`/event/${eventId}`)
}
</script>

<style scoped lang="scss">
.dashboard-container {
  padding: 30px;
  background-color: var(--el-bg-color-page);
  min-height: 100vh;
}

.dashboard-header {
  margin-bottom: 30px;

  .title-bar {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-top: 15px;

    h1 {
      margin: 0 0 10px 0;
      font-size: 28px;
      font-weight: 700;
    }

    .meta-tags {
      display: flex;
      align-items: center;
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

    .label {
      color: var(--el-text-color-secondary);
      font-size: 14px;
    }

    .value {
      font-size: 26px;
      font-weight: bold;
      margin-top: 8px;
    }

    &.highlight {
      border-left: 4px solid var(--el-color-primary);
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
  cursor: default;

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