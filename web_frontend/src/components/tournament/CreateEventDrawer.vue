<template>
  <el-drawer
      v-model="visible"
      title="创建竞赛项目"
      size="500px"
      @closed="resetForm"
  >
    <el-form :model="form" :rules="rules" ref="formRef" label-position="top">
      <el-form-item label="项目名称" prop="event_name">
        <el-input v-model="form.event_name" placeholder="例如：U14 男子重剑个人赛"/>
      </el-form-item>

      <el-form-item label="剑种类型" prop="event_type_id">
        <el-select v-model="form.event_type_id" placeholder="请选择剑种" style="width: 100%">
          <el-option v-for="t in EVENT_TYPES" :key="t.id" :label="t.name" :value="t.id"/>
        </el-select>
      </el-form-item>

      <el-form-item label="应用规则" prop="rule_id">
        <el-select v-model="form.rule_id" placeholder="请选择赛制规则" style="width: 100%">
          <el-option v-for="r in FENCING_RULES" :key="r.id" :label="r.name" :value="r.id"/>
        </el-select>
      </el-form-item>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="比赛性质" prop="is_team_event">
            <el-radio-group v-model="form.is_team_event">
              <el-radio-button :label="false">个人赛</el-radio-button>
              <el-radio-button :label="true">团体赛</el-radio-button>
            </el-radio-group>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="预定开始时间" prop="start_time">
            <el-time-picker
                v-model="form.start_time"
                placeholder="选择时间"
                style="width: 100%"
                format="HH:mm"
                value-format="YYYY-MM-DD HH:mm:ss"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-alert
          title="提示"
          description="创建项目后，您将进入选手录入与小组编排环节。"
          type="info"
          show-icon
          :closable="false"
      />
    </el-form>

    <template #footer>
      <div style="flex: auto">
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleConfirm">确认创建</el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import {ref, reactive} from 'vue'
import {EVENT_TYPES, FENCING_RULES} from '@/types/event.ts'
import {ElMessage} from 'element-plus'

const props = defineProps<{ tournamentId: string }>()
const visible = defineModel<boolean>()
const loading = ref(false)
const formRef = ref()

const form = reactive({
  event_name: '',
  event_type_id: '',
  rule_id: '',
  is_team_event: false,
  start_time: ''
})

const rules = {
  event_name: [{required: true, message: '请输入项目名称', trigger: 'blur'}],
  event_type_id: [{required: true, message: '请选择剑种', trigger: 'change'}],
  rule_id: [{required: true, message: '请选择规则', trigger: 'change'}]
}

const handleConfirm = async () => {
  await formRef.value.validate(async (valid: boolean) => {
    if (valid) {
      loading.value = true
      // 这里的 payload 完全对应你的后端 Event 表
      const payload = {
        ...form,
        tournament_id: props.tournamentId,
        status_id: 'status-pending-uuid', // 默认为待开始
      }

      try {
        console.log('发送给 Django API:', payload)
        await new Promise(r => setTimeout(r, 800)) // 模拟网络
        ElMessage.success('竞赛项目创建成功')
        visible.value = false
        // 这里可以触发一个父组件的刷新事件
      } finally {
        loading.value = false
      }
    }
  })
}

const resetForm = () => {
  if (formRef.value) formRef.value.resetFields()
}
</script>