<template>
  <div class="create-page-wrapper">
    <AppHeader :showCreate="false"/>

    <div class="form-container">
      <el-card class="form-card">
        <template #header>
          <div class="form-title">
            <h2>🏆 {{ $t('tournament.createTitle') }}</h2>
          </div>
        </template>

        <TournamentForm ref="tournamentFormRef"/>

        <div class="form-actions">
          <el-button @click="router.back()">{{ $t('common.actions.cancel') }}</el-button>
          <el-button type="primary" :loading="loading" @click="handleCreate">
            {{ $t('tournament.actions.createAndEnter') }}
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
/* 1. 确保所有需要的引用都已导入 */
import {reactive, ref} from 'vue'
import {useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'
import AppHeader from '@/components/layout/AppHeader.vue'
import i18n from '@/locales'
import {DataManager} from '@/services/DataManager'
import TournamentForm from '@/components/tournament/TournamentForm.vue'

const router = useRouter()
const loading = ref(false)

const tournamentFormRef = ref<InstanceType<typeof TournamentForm>>()

/* 4. 定义 handleCreate 函数 (解决 Property 'handleCreate' does not exist 报错) */
const handleCreate = async () => {
  if (!tournamentFormRef.value) {return;}

  // 【关键修改】4. 调用子组件暴露的 validate 方法
  const isValid = await tournamentFormRef.value.validate();
  if (isValid) {
    loading.value = true;
    try {
      // 【关键修改】5. 获取子组件暴露的 formData
      const result = await DataManager.createTournament(tournamentFormRef.value.formData);
      ElMessage.success('赛事创建成功！');
      await router.push(`/tournament/${result.id}`); // 直接进入新创建的赛事
    } catch (error) {
      console.error(error);
      ElMessage.error('创建失败');
    } finally {
      loading.value = false;
    }
  }
}
</script>

<style scoped lang="scss">
.create-page-wrapper {
  min-height: 100vh;
  background-color: var(--el-bg-color-page);
}

.form-container {
  max-width: 800px;
  margin: 40px auto;

  .form-card {
    border-radius: 16px;
    padding: 20px;
  }

  .form-title {
    h2 {
      margin: 0;
      font-size: 24px;
      color: var(--el-text-color-primary);
    }

    p {
      margin: 8px 0 0;
      color: var(--el-text-color-secondary);
    }
  }

  .form-actions {
    margin-top: 40px;
    display: flex;
    justify-content: flex-end;
    gap: 12px;
  }
}
</style>