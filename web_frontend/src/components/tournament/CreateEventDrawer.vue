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
        <el-select v-model="form.event_type_id" :placeholder="$t('tournament.eventDrawer.placeholder.eventType')" style="width: 100%">
          <el-option v-for="t in EVENT_TYPES" :key="t.id" :label="t.name" :value="t.id"/>
        </el-select>
      </el-form-item>

      <el-form-item :label="$t('tournament.eventDrawer.form.rule')" prop="rule_id">
        <el-select v-model="form.rule_id" :placeholder="$t('tournament.eventDrawer.placeholder.rule')" style="width: 100%">
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
        <el-button type="primary" :loading="loading" @click="handleConfirm">{{ $t('tournament.eventDrawer.actions.confirmCreate') }}</el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import {ref, reactive} from 'vue'
import {EVENT_TYPES, FENCING_RULES} from '@/types/event.ts'
import {ElMessage} from 'element-plus'
import i18n from '@/locales'

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
  event_name: [{required: true, message: () => i18n.global.t('tournament.eventDrawer.messages.eventNameRequired'), trigger: 'blur'}],
  event_type_id: [{required: true, message: () => i18n.global.t('tournament.eventDrawer.messages.eventTypeRequired'), trigger: 'change'}],
  rule_id: [{required: true, message: () => i18n.global.t('tournament.eventDrawer.messages.ruleRequired'), trigger: 'change'}]
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
        ElMessage.success(i18n.global.t('tournament.eventDrawer.messages.createSuccess'))
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