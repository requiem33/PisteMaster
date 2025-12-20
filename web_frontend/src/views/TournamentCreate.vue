<template>
  <div class="create-page-wrapper">
    <div class="header-nav">
      <el-button icon="Back" @click="router.back()">返回首页</el-button>
    </div>

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
import {reactive, ref} from 'vue'
import {useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'

const router = useRouter()
const loading = ref(false)

const form = reactive({
  tournament_name: '',
  organizer: '',
  location: '',
  date_range: [] as string[]
})

const rules = {
  tournament_name: [{required: true, message: '赛事名称不能为空', trigger: 'blur'}],
  date_range: [{required: true, message: '请选择比赛日期', trigger: 'change'}]
}

const handleCreate = async () => {
  loading.value = true
  try {
    // 模拟 Django API 调用
    console.log('正在向后端发送 UUID 格式请求...', form)
    await new Promise(r => setTimeout(r, 1000))

    // 假设后端返回了新生成的 UUID: '550e8400-e29b-41d4-a716-446655440000'
    const newId = '550e8400-e29b-41d4-a716-446655440000'

    ElMessage.success('赛事创建成功')
    // 👈 关键跳转：直接带 ID 进入 Dashboard
    router.push(`/tournament/${newId}`)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.create-page-wrapper {
  min-height: 100vh;
  background-color: var(--el-bg-color-page);
  padding: 40px 20px;
}

.header-nav {
  max-width: 800px;
  margin: 0 auto 20px;
}

.form-container {
  max-width: 800px;
  margin: 0 auto;

  .form-card {
    border-radius: 16px;
    padding: 20px;
  }

  .form-title {
    h2 {
      margin: 0;
      font-size: 24px;
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