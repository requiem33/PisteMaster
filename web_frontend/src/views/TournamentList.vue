<template>
  <div class="tournament-list-page">
    <AppHeader :showCreate="true" @create="createNewTournament">
      <template #extra>
        <el-breadcrumb separator-class="el-icon-arrow-right" class="header-breadcrumb">
          <el-breadcrumb-item :to="{ path: '/' }">{{ $t('tournament.dashboard.breadcrumb.home') }}</el-breadcrumb-item>
          <el-breadcrumb-item>{{ $t('tournament.dashboard.breadcrumb.tournamentList') }}</el-breadcrumb-item>
        </el-breadcrumb>
      </template>
    </AppHeader>

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

      <div v-loading="loading">
        <el-row :gutter="20" class="tournament-grid">
          <el-col
              v-for="item in filteredTournaments"
              :key="item.id"
              :xs="24" :sm="12" :md="8" :lg="6"
          >
            <!-- 【关键修复】将卡片包裹，分离点击区域 -->
            <el-card shadow="hover" class="event-card">
              <!-- 1. 主要内容区域，负责点击跳转 -->
              <div class="card-main-content" @click="goToDashboard(item.id)">
                <div class="card-status">
                  <el-tag :type="item.status === 'completed' ? 'info' : 'success'" size="small">
                    {{ item.status === 'completed' ? $t('common.completed') : $t('common.ongoing') }}
                  </el-tag>
                  <el-tag v-if="!item.is_synced" type="warning" size="small" effect="plain" class="ml-10">
                    {{ $t('common.offline') || '离线' }}
                  </el-tag>
                </div>
                <h3 class="event-name">{{ item.tournament_name }}</h3>
                <div class="meta-info">
                  <p class="event-meta">
                    <el-icon>
                      <Calendar/>
                    </el-icon>
                    {{ item.start_date }} ~ {{ item.end_date }}
                  </p>
                  <p class="event-meta">
                    <el-icon>
                      <Tickets/>
                    </el-icon>
                    项目总数: {{ item.eventCount || 0 }}
                  </p>
                  <p class="event-meta">
                    <el-icon>
                      <User/>
                    </el-icon>
                    选手总数: {{ item.fencerCount || 0 }}
                  </p>
                </div>
              </div>

              <!-- 2. 卡片底部，负责独立操作 -->
              <template #footer>
                <div class="card-footer">
                  <span class="rule-type">{{ item.organizer }}</span>
                  <div class="footer-actions">
                    <!-- 3. 【新增】删除按钮，并使用 .stop 阻止事件冒泡 -->
                    <el-button
                        type="danger"
                        icon="Delete"
                        circle
                        plain
                        @click.stop="handleDeleteTournament(item.id, item.tournament_name)"
                    />
                    <el-button link type="primary" @click="goToDashboard(item.id)">
                      {{ $t('common.enterOrchestration') }}
                      <el-icon>
                        <ArrowRight/>
                      </el-icon>
                    </el-button>
                  </div>
                </div>
              </template>
            </el-card>
          </el-col>
        </el-row>
        <el-empty v-if="!loading && filteredTournaments.length === 0" :description="$t('common.noMatch')"/>
      </div>
    </main>
  </div>
</template>


<script setup lang="ts">
import {ref, computed, onMounted} from 'vue'
import {useRouter} from 'vue-router'
import {Search, Calendar, User, ArrowRight, Tickets} from '@element-plus/icons-vue' // 引入新图标
import AppHeader from '@/components/layout/AppHeader.vue'
import {DataManager} from '@/services/DataManager';
import {ElMessage, ElMessageBox} from "element-plus";

const router = useRouter()
const loading = ref(false)
const searchQuery = ref('')
const statusFilter = ref('all')
const tournaments = ref<any[]>([])

// 【关键修复】2. 更新数据加载函数
const loadTournaments = async () => {
  loading.value = true;
  try {
    // 调用我们新创建的、能获取完整信息的方法
    const result = await DataManager.getTournamentListWithDetails();
    tournaments.value = result ?? [];
  } catch (error) {
    console.error('Failed to load tournaments with details:', error);
    tournaments.value = [];
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadTournaments()
})

const filteredTournaments = computed(() => {
  return tournaments.value.filter(t => {
    const name = t.tournament_name || ''
    const matchesSearch = name.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchesStatus = statusFilter.value === 'all' || t.status === statusFilter.value
    return matchesSearch && matchesStatus
  })
})

const createNewTournament = () => {
  router.push('/tournament/create')
}

const handleDeleteTournament = async (tournamentId: string, tournamentName: string) => {
  try {
    await ElMessageBox.confirm(
        `确定要永久删除赛事 “<strong>${tournamentName}</strong>” 吗？<br/>此操作将同时删除该赛事下的所有项目和成绩，且不可恢复。`,
        '危险操作确认',
        {
          confirmButtonText: '确认删除',
          cancelButtonText: '取消',
          type: 'warning',
          dangerouslyUseHTMLString: true,
        }
    );

    loading.value = true;
    await DataManager.deleteTournament(tournamentId);
    ElMessage.success('赛事已删除');
    loadTournaments(); // 重新加载列表
  } catch (error) {
    if (error !== 'cancel') {
      console.error("删除赛事失败:", error);
      ElMessage.error('删除失败');
    }
  } finally {
    if (loading.value) loading.value = false;
  }
};


const goToDashboard = (id: string) => {
  router.push(`/tournament/${id}`)
}
</script>

<style scoped lang="scss">
.event-card {
  // ...
  .card-main-content {
    cursor: pointer; // 明确告诉用户这块区域可点
  }

  .card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .rule-type {
      font-size: 12px;
      color: var(--el-text-color-placeholder);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      margin-right: 10px;
    }

    .footer-actions {
      display: flex;
      align-items: center;
      gap: 8px; // 为按钮之间增加一些间距
      flex-shrink: 0; // 防止按钮被压缩
    }
  }
}

.tournament-list-page {
  min-height: 100vh;
  background-color: var(--el-bg-color-page);
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

  .ml-10 {
    margin-left: 10px;
  }
}

.event-card {
  height: 100%;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 20px;

  &:hover {
    transform: translateY(-4px);
    box-shadow: var(--el-box-shadow-light);
  }

  .card-status {
    display: flex;
    justify-content: flex-start;
    margin-bottom: 12px;
  }

  .event-name {
    margin: 10px 0;
    font-size: 16px;
    font-weight: 600;
    min-height: 44px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .event-meta {
    font-size: 13px;
    color: var(--el-text-color-secondary);
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 6px 0;
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