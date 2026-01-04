<template>
  <div class="tournament-list-page">
    <AppHeader :title="$t('tournament.listTitle')" :showCreate="true" @create="createNewEvent"/>

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
            <el-card shadow="hover" class="event-card" @click="goToOrchestrator(item.id)">
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
                    <User/>
                  </el-icon>
                  {{ $t('common.fencerCount') }}: {{ item.fencerCount || 0 }}
                </p>
              </div>

              <template #footer>
                <div class="card-footer">
                  <span class="rule-type">{{ item.organizer }}</span>
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

        <el-empty v-if="!loading && filteredTournaments.length === 0" :description="$t('common.noMatch')"/>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import {ref, computed, onMounted} from 'vue'
import {useRouter} from 'vue-router'
import {Search, Calendar, User, ArrowRight} from '@element-plus/icons-vue'
import AppHeader from '@/components/layout/AppHeader.vue'
// 导入存储服务
import {DataManager} from '@/services/DataManager';

const router = useRouter()
const loading = ref(false)

// --- 搜索与过滤 ---
const searchQuery = ref('')
const statusFilter = ref('all')
const tournaments = ref<any[]>([])

// --- 获取数据 ---
const loadTournaments = async () => {
  loading.value = true;
  try {
    // 即使 DataManager 报错返回了 undefined，这里也会保证赋值为 []
    const result = await DataManager.getTournamentList();
    tournaments.value = result ?? [];

    // 排序前加一个判断，增强健壮性
    if (tournaments.value.length > 0) {
      tournaments.value.sort((a, b) =>
          (b.updated_at || 0) - (a.updated_at || 0)
      );
    }
  } catch (error) {
    console.error('Failed to load:', error);
    tournaments.value = []; // 错误时清空或保持原状
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

const createNewEvent = () => {
  router.push('/tournament/create')
}

const goToOrchestrator = (id: string) => {
  // 确保跳转路径与路由器配置一致
  router.push(`/tournament/${id}`)
}
</script>

<style scoped lang="scss">
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