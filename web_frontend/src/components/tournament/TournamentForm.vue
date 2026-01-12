<!-- src/components/tournament/TournamentForm.vue -->
<template>
  <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-position="top"
      size="large"
  >
    <el-form-item label="赛事名称" prop="tournament_name">
      <el-input v-model="formData.tournament_name" placeholder="例如：2024 全国击剑冠军赛"/>
    </el-form-item>
    <el-form-item label="举办地点" prop="location">
      <el-input v-model="formData.location" placeholder="例如：江苏省 南京市"/>
    </el-form-item>
    <el-form-item label="举办日期" prop="date_range">
      <el-date-picker
          v-model="formData.date_range"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 100%"
          value-format="YYYY-MM-DD"
      />
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import {ref, reactive, watch} from 'vue'
import type {FormInstance, FormRules} from 'element-plus'

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
  tournament_name: [{required: true, message: '赛事名称不能为空', trigger: 'blur'}],
  date_range: [{required: true, message: '举办日期不能为空', trigger: 'change'}]
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
