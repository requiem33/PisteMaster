<template>
  <el-drawer
      v-model="visible"
      :title="$t('tournament.eventDrawer.title')"
      size="500px"
      @closed="resetForm"
  >
    <el-form :model="form" :rules="rules" ref="formRef" label-position="top">
      <el-form-item :label="$t('tournament.eventDrawer.form.eventName')" prop="event_name">
        <el-input v-model="form.event_name" :placeholder="$t('tournament.eventDrawer.placeholder.eventName')"/>
      </el-form-item>

      <el-form-item :label="$t('tournament.eventDrawer.form.eventType')" prop="event_type_id">
        <el-select v-model="form.event_type_id" :placeholder="$t('tournament.eventDrawer.placeholder.eventType')"
                   style="width: 100%">
          <el-option v-for="t in EVENT_TYPES" :key="t.id" :label="t.name" :value="t.id"/>
        </el-select>
      </el-form-item>

      <el-form-item :label="$t('tournament.eventDrawer.form.rule')" prop="rule_id">
        <el-select v-model="form.rule_id" :placeholder="$t('tournament.eventDrawer.placeholder.rule')"
                   style="width: 100%">
          <el-option v-for="r in FENCING_RULES" :key="r.id" :label="r.name" :value="r.id"/>
        </el-select>
      </el-form-item>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item :label="$t('tournament.eventDrawer.form.eventNature')" prop="is_team_event">
            <el-radio-group v-model="form.is_team_event">
              <el-radio-button :label="false">{{ $t('tournament.eventDrawer.form.individual') }}</el-radio-button>
              <el-radio-button :label="true">{{ $t('tournament.eventDrawer.form.team') }}</el-radio-button>
            </el-radio-group>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="$t('tournament.eventDrawer.form.startTime')" prop="start_time">
            <el-time-picker
                v-model="form.start_time"
                :placeholder="$t('tournament.eventDrawer.placeholder.startTime')"
                style="width: 100%"
                format="HH:mm"
                value-format="YYYY-MM-DD HH:mm:ss"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-alert
          :title="$t('tournament.eventDrawer.alert.title')"
          :description="$t('tournament.eventDrawer.alert.description')"
          type="info"
          show-icon
          :closable="false"
      />
    </el-form>

    <template #footer>
      <div style="flex: auto">
        <el-button @click="visible = false">{{ $t('tournament.eventDrawer.actions.cancel') }}</el-button>
        <el-button type="primary" :loading="loading" @click="handleConfirm">
          {{ $t('tournament.eventDrawer.actions.confirmCreate') }}
        </el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import {ref, reactive} from 'vue'
import {EVENT_TYPES, FENCING_RULES} from '@/types/event.ts'
import {ElMessage} from 'element-plus'
import i18n from '@/locales'
import {DataManager} from '@/services/DataManager' // 导入数据管理器

// 定义 Props
const props = defineProps<{
  tournamentId: string
}>()

// 定义 Emits，用于通知父组件刷新
const emit = defineEmits<{
  (e: 'success'): void
}>()

// v-model 控制显示隐藏
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
  event_name: [{
    required: true,
    message: () => i18n.global.t('tournament.eventDrawer.messages.eventNameRequired'),
    trigger: 'blur'
  }],
  event_type_id: [{
    required: true,
    message: () => i18n.global.t('tournament.eventDrawer.messages.eventTypeRequired'),
    trigger: 'change'
  }],
  rule_id: [{
    required: true,
    message: () => i18n.global.t('tournament.eventDrawer.messages.ruleRequired'),
    trigger: 'change'
  }]
}

const handleConfirm = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid: boolean) => {
    if (valid) {
      loading.value = true

      // 准备存储载体
      const payload = {
        ...form,
        tournament_id: props.tournamentId,
        // 这里可以根据 rule_id 或 event_type_id 从常量库中匹配名称，方便列表显示
        rule_name: FENCING_RULES.find(r => r.id === form.rule_id)?.name || '未知规则',
      }

      try {
        // 调用 DataManager 写入 IndexedDB (events 表)
        await DataManager.createEvent(payload)

        ElMessage.success(i18n.global.t('tournament.eventDrawer.messages.createSuccess'))

        // 操作成功后的处理：
        // 1. 关闭抽屉
        visible.value = false
        // 2. 通知父组件 (Dashboard) 重新加载列表
        emit('success')

      } catch (error) {
        console.error('Failed to create event:', error)
        ElMessage.error('创建项目失败，请重试')
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