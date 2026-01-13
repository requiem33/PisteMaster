<!-- src/components/tournament/EditEventDrawer.vue -->
<template>
  <el-drawer
      :model-value="modelValue"
      title="编辑项目信息"
      size="600px"
      @update:model-value="$emit('update:modelValue', $event)"
  >
    <EventForm ref="eventFormRef" :initial-data="eventData"/>
    <template #footer>
      <div style="text-align: right;">
        <el-button @click="$emit('update:modelValue', false)">取消</el-button>
        <el-button type="primary" :loading="isSubmitting" @click="submitForm">保存更新</el-button>
      </div>
    </template>
  </el-drawer>
</template>
<script setup lang="ts">
import {ref} from 'vue'
import {DataManager} from '@/services/DataManager'
import {ElMessage} from 'element-plus'
import EventForm from './EventForm.vue'

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
        rule_name: data.rules.preset === 'world_cup' ? '世界杯' : data.rules.preset === 'olympics' ? '奥运会' : '自定义'
      })
      ElMessage.success('更新成功')
      emit('success')
      emit('update:modelValue', false)
    } catch (e) {
      ElMessage.error('更新失败')
    } finally {
      isSubmitting.value = false
    }
  }
}
</script>