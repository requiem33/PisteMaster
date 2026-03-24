<template>
  <el-drawer
      v-model="visible"
      :title="$t('tournament.eventDrawer.title')"
      size="600px"
      @closed="resetForm"
  >
    <EventForm ref="eventFormRef"/>

    <template #footer>
      <div style="flex: auto; text-align: right;">
        <el-button @click="visible = false">{{ $t('tournament.eventDrawer.actions.cancel') }}</el-button>
        <el-button type="primary" :loading="loading" @click="handleConfirm">
          {{ $t('tournament.eventDrawer.actions.confirmCreate') }}
        </el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import {ref} from 'vue'
import {ElMessage} from 'element-plus'
import {DataManager} from '@/services/DataManager'
import EventForm from './EventForm.vue'

const props = defineProps<{ tournamentId: string }>()
const emit = defineEmits<{ (e: 'success'): void }>()
const visible = defineModel<boolean>()

const loading = ref(false)
const eventFormRef = ref<InstanceType<typeof EventForm>>()

const handleConfirm = async () => {
  const isValid = await eventFormRef.value?.validate()
  if (isValid) {
    loading.value = true
    try {
      const data = eventFormRef.value!.formData
      await DataManager.createEvent({
        tournament_id: props.tournamentId,
        event_name: data.event_name,
        event_type: `${data.gender}_${data.weapon}`,
        is_team_event: data.is_team_event,
        start_time: data.start_time,
        rule_mode: data.rule_mode,
        rule_id: data.rule_id,
        rules: data.rules
      })
      ElMessage.success('项目创建成功')
      visible.value = false
      emit('success')
    } catch (_e) {
      ElMessage.error('创建失败')
    } finally {
      loading.value = false
    }
  }
}

const resetForm = () => {
}
</script>
