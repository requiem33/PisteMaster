<template>
  <div class="create-page-wrapper">
    <AppHeader :title="$t('tournament.createTitle')" :showCreate="false"/>

    <div class="form-container">
      <el-card class="form-card">
        <template #header>
          <div class="form-title">
            <h2>🏆 {{ $t('tournament.createTitle') }}</h2>
          </div>
        </template>

        <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-position="top"
            size="large"
        >
          <el-form-item :label="$t('tournament.form.name')" prop="tournament_name">
            <el-input v-model="form.tournament_name" :placeholder="$t('tournament.form.placeholder.name')"/>
          </el-form-item>

          <el-form-item :label="$t('tournament.form.organizer')" prop="organizer">
            <el-input v-model="form.organizer" :placeholder="$t('tournament.form.placeholder.organizer')"/>
          </el-form-item>

          <el-form-item :label="$t('tournament.form.location')" prop="location">
            <el-input v-model="form.location" :placeholder="$t('tournament.form.placeholder.location')"/>
          </el-form-item>

          <el-form-item :label="$t('tournament.form.date')" prop="date_range">
            <el-date-picker
                v-model="form.date_range"
                type="daterange"
                :range-separator="$t('tournament.form.rangeSeparator')"
                :start-placeholder="$t('tournament.form.startPlaceholder')"
                :end-placeholder="$t('tournament.form.endPlaceholder')"
                style="width: 100%"
                value-format="YYYY-MM-DD"
            />
          </el-form-item>

          <div class="form-actions">
            <el-button @click="router.back()">{{ $t('common.actions.cancel') }}</el-button>
            <el-button type="primary" :loading="loading" @click="handleCreate">
              {{ $t('tournament.actions.createAndEnter') }}
            </el-button>
          </div>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
/* 1. 确保所有需要的引用都已导入 */
import {reactive, ref} from 'vue'
import {useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'
import type {FormInstance, FormRules} from 'element-plus'
import AppHeader from '@/components/layout/AppHeader.vue'
import i18n from '@/locales'
import {DataManager} from '@/services/DataManager'

const router = useRouter()
const loading = ref(false)
const formRef = ref<FormInstance>() // 表单引用

/* 2. 定义 form 变量 (解决 Property 'form' does not exist 报错) */
const form = reactive({
  tournament_name: '',
  organizer: '',
  location: '',
  date_range: [] as string[]
})

/* 3. 定义 rules (解决 Property 'rules' does not exist 报错) */
const rules: FormRules = {
  tournament_name: [{
    required: true,
    message: () => i18n.global.t('tournament.messages.nameRequired'),
    trigger: 'blur'
  }],
  date_range: [{required: true, message: () => i18n.global.t('tournament.messages.dateRequired'), trigger: 'change'}]
}

/* 4. 定义 handleCreate 函数 (解决 Property 'handleCreate' does not exist 报错) */
const handleCreate = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        // 调用中控层进行存储
        const result = await DataManager.createTournament(form);

        ElMessage.success(i18n.global.t('tournament.messages.createSuccess'));

        // 跳转到赛事列表
        await router.push('/tournament');
      } catch (error) {
        console.error(error);
        ElMessage.error(i18n.global.t('tournament.messages.createFailed'));
      } finally {
        loading.value = false
      }
    }
  })
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