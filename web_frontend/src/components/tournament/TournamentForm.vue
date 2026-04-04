<!-- src/components/tournament/TournamentForm.vue -->
<template>
  <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-position="top"
      size="large"
  >
    <el-form-item :label="$t('tournament.form.name')" prop="tournament_name">
      <el-input v-model="formData.tournament_name" :placeholder="$t('tournament.form.placeholder.name')"/>
    </el-form-item>
    <el-form-item :label="$t('tournament.form.location')" prop="location">
      <el-input v-model="formData.location" :placeholder="$t('tournament.form.placeholder.location')"/>
    </el-form-item>
    <el-form-item :label="$t('tournament.form.date')" prop="date_range">
      <el-date-picker
          v-model="formData.date_range"
          type="daterange"
          :range-separator="$t('tournament.form.rangeSeparator')"
          :start-placeholder="$t('tournament.form.startPlaceholder')"
          :end-placeholder="$t('tournament.form.endPlaceholder')"
          style="width: 100%"
          value-format="YYYY-MM-DD"
      />
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import {ref, reactive, watch} from 'vue'
import {useI18n} from 'vue-i18n'
import type {FormInstance, FormRules} from 'element-plus'

const {t} = useI18n()

// --- 1. 定义 Props ---
const props = defineProps<{
  // 接收外部传入的初始数据，用于“编辑”模式
  initialData?: any
}>()

// --- 2. 定义内部响应式数据 ---
const formRef = ref<FormInstance>()
const formData = reactive({
  id: '',
  tournament_name: '',
  location: '',
  date_range: [] as string[]
})
const rules: FormRules = {
  tournament_name: [{required: true, message: t('tournament.messages.nameRequired'), trigger: 'blur'}],
  date_range: [{required: true, message: t('tournament.messages.dateRequired'), trigger: 'change'}]
}

// --- 3. 监听外部数据，填充表单 ---
watch(() => props.initialData, (newData) => {
  if (newData && newData.id) { // 只有在编辑模式（有ID）时才填充
    formData.id = newData.id
    formData.tournament_name = newData.tournament_name
    formData.location = newData.location
    formData.date_range = [newData.start_date, newData.end_date].filter(Boolean) as string[]
  } else {
    // 如果是创建模式，重置表单
    formRef.value?.resetFields()
    formData.id = ''
  }
}, {immediate: true, deep: true});

// --- 4. 暴露方法给父组件 ---
const validate = () => {
  return formRef.value?.validate()
}

// 使用 defineExpose 将数据和方法暴露出去
defineExpose({
  formData,
  validate
})
</script>
