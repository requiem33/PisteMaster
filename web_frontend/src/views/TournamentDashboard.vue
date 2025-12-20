<template>
  <div class="dashboard-container">
    <div class="tournament-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">赛事中心</el-breadcrumb-item>
        <el-breadcrumb-item>赛事详情</el-breadcrumb-item>
      </el-breadcrumb>

      <div class="title-section">
        <h1>{{ tournamentData.tournament_name }}</h1>
        <div class="meta">
          <el-tag effect="plain">{{ tournamentData.organizer }}</el-tag>
          <span><el-icon><Location/></el-icon> {{ tournamentData.location }}</span>
          <span><el-icon><Calendar/></el-icon> {{ tournamentData.start_date }} 至 {{ tournamentData.end_date }}</span>
        </div>
      </div>
    </div>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6" v-for="stat in stats" :key="stat.label">
        <el-card shadow="never">
          <div class="stat-content">
            <div class="label">{{ stat.label }}</div>
            <div class="value">{{ stat.value }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <div class="events-section">
      <div class="section-header">
        <h2>竞赛项目 (Events)</h2>
        <el-button type="primary" icon="Plus" @click="openCreateEvent">新增单项</el-button>
      </div>

      <el-empty v-if="events.length === 0" description="暂无竞赛项目，请先创建一个">
        <el-button type="primary" @click="openCreateEvent">立刻创建</el-button>
      </el-empty>

      <el-row :gutter="20" v-else>
        <el-col :span="8" v-for="event in events" :key="event.id">
          <el-card class="event-card" hoverable>
            <template #header>
              <div class="card-header">
                <strong>{{ event.name }}</strong>
                <el-tag size="small">{{ event.status }}</el-tag>
              </div>
            </template>
            <div class="event-info">
              <p>选手人数: {{ event.fencerCount }}</p>
              <p>规则: {{ event.rule }}</p>
            </div>
            <div class="card-actions">
              <el-button type="primary" @click="goToOrchestrator(event.id)">进入编排工作流</el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<style scoped lang="scss">
.dashboard-container {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.tournament-header {
  margin-bottom: 30px;

  .title-section {
    margin-top: 16px;

    h1 {
      font-size: 28px;
      margin: 0 0 12px 0;
    }

    .meta {
      color: var(--el-text-color-secondary);
      display: flex;
      gap: 20px;
      align-items: center;
    }
  }
}

.stats-row {
  margin-bottom: 40px;

  .stat-content {
    .label {
      font-size: 14px;
      color: var(--el-text-color-secondary);
    }

    .value {
      font-size: 24px;
      font-weight: bold;
      margin-top: 4px;
    }
  }
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.event-card {
  margin-bottom: 20px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .event-info {
    font-size: 14px;
    color: var(--el-text-color-regular);
    margin-bottom: 15px;
  }

  .card-actions {
    border-top: 1px solid var(--el-border-color-lighter);
    padding-top: 15px;
  }
}
</style>