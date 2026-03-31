<!-- src/components/tournament/EditEventDrawer.vue -->
<template>
  <el-drawer
      :model-value="modelValue"
      :title="$t('tournament.editEventDrawer.title')"
      size="600px"
      @update:model-value="$emit('update:modelValue', $event)"
  >
    <EventForm ref="eventFormRef" :initial-data="eventData"/>
    <template #footer>
      <div style="text-align: right;">
        <el-button @click="$emit('update:modelValue', false)">{{ $t('common.actions.cancel') }}</el-button>
        <el-button type="primary" :loading="isSubmitting" @click="submitForm">{{ $t('common.actions.save') }}</el-button>
      </div>
    </template>
  </el-drawer>
</template>
<script setup lang="ts">
import {ref} from 'vue'
import {useI18n} from 'vue-i18n'
import {DataManager} from '@/services/DataManager'
import {ElMessage} from 'element-plus'
import EventForm from './EventForm.vue'

const {t} = useI18n()

const props = defineProps<{ modelValue: boolean, eventData: any }>()
const emit = defineEmits(['update:modelValue', 'success'])

const isSubmitting = ref(false)
const eventFormRef = ref<InstanceType<typeof EventForm>>()

const submitForm = async () => {
  const isValid = await eventFormRef.value?.validate()
  if (isValid) {
    isSubmitting.value = true
    try {
      const data = eventFormRef.value!.formData
      await DataManager.updateEvent(props.eventData.id, {
        ...data,
        rule_name: data.rules.preset === 'world_cup' ? t('event.ruleSettings.worldCup') : data.rules.preset === 'olympics' ? t('event.ruleSettings.olympics') : t('event.ruleSettings.custom')
      })
      ElMessage.success(t('tournament.editEventDrawer.updateSuccess'))
      emit('success')
      emit('update:modelValue', false)
    } catch (_e) {
      ElMessage.error(t('tournament.editEventDrawer.updateFailed'))
    } finally {
      isSubmitting.value = false
    }
  }
}
</script>