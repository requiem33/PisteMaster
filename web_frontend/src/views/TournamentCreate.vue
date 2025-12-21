<template>
  <div class="create-page-wrapper">
    <AppHeader title="创建赛事" :showCreate="false"/>

    <div class="form-container">
      <el-card class="form-card">
        <template #header>
          <div class="form-title">
            <h2>🏆 开启新赛事</h2>
            <p>请填写赛事的基础信息，完成后即可开始编排单项</p>
          </div>
        </template>

        <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-position="top"
            size="large"
        >
          <el-form-item label="赛事名称" prop="tournament_name">
            <el-input v-model="form.tournament_name" placeholder="输入完整赛事名称"/>
          </el-form-item>

          <el-form-item label="主办单位" prop="organizer">
            <el-input v-model="form.organizer" placeholder="组织机构或俱乐部名称"/>
          </el-form-item>

          <el-form-item label="举办地点" prop="location">
            <el-input v-model="form.location" placeholder="比赛场馆地址"/>
          </el-form-item>

          <el-form-item label="起止日期" prop="date_range">
            <el-date-picker
                v-model="form.date_range"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                style="width: 100%"
                value-format="YYYY-MM-DD"
            />
          </el-form-item>

          <div class="form-actions">
            <el-button @click="router.back()">取消</el-button>
            <el-button type="primary" :loading="loading" @click="handleCreate">
              立即创建并进入管理台
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
  tournament_name: [{required: true, message: '赛事名称不能为空', trigger: 'blur'}],
  date_range: [{required: true, message: '请选择比赛日期', trigger: 'change'}]
}

/* 4. 定义 handleCreate 函数 (解决 Property 'handleCreate' does not exist 报错) */
const handleCreate = async () => {
  if (!formRef.value) return

  // 校验表单
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        console.log('正在提交赛事数据:', form)
        // 模拟 API 延迟
        await new Promise(r => setTimeout(r, 1000))

        const newId = '550e8400-e29b-41d4-a716-446655440000'
        ElMessage.success('赛事创建成功')

        // 跳转到编排总控制台（假设路由已配置）
        router.push(`/orchestrator/${newId}`)
      } catch (error) {
        ElMessage.error('创建失败，请重试')
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