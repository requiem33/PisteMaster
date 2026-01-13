<!-- src/components/tournament/EventForm.vue -->
<template>
  <el-form :model="formData" :rules="formRules" ref="formRef" label-position="top">
    <!-- 1. 基础信息 -->
    <el-row :gutter="20">
      <el-col :span="12">
        <el-form-item label="项目名称" prop="event_name">
          <el-input v-model="formData.event_name" placeholder="如：男子重剑个人"/>
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="比赛时间" prop="start_time">
          <el-date-picker
              v-model="formData.start_time"
              type="datetime"
              placeholder="选择开始时间"
              style="width: 100%"
              value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="8">
        <el-form-item label="剑种" prop="weapon">
          <el-select v-model="formData.weapon" placeholder="请选择" style="width: 100%">
            <el-option label="重剑 (Epee)" value="Epee"/>
            <el-option label="花剑 (Foil)" value="Foil"/>
            <el-option label="佩剑 (Sabre)" value="Sabre"/>
          </el-select>
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="性别" prop="gender">
          <el-select v-model="formData.gender" placeholder="请选择" style="width: 100%">
            <el-option label="男 (M)" value="M"/>
            <el-option label="女 (F)" value="F"/>
            <el-option label="混合 (X)" value="X"/>
          </el-select>
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="类型" prop="is_team_event">
          <el-radio-group v-model="formData.is_team_event" size="small">
            <el-radio-button :label="false">个人</el-radio-button>
            <el-radio-button :label="true">团体</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-col>
    </el-row>

    <el-divider content-position="left">赛制规则配置</el-divider>

    <!-- 2. 规则配置 (嵌入 RuleSettings) -->
    <RuleSettings v-model="formData.rules"/>
  </el-form>
</template>

<script setup lang="ts">
import {ref, reactive, watch} from 'vue'
import type {FormInstance, FormRules} from 'element-plus'
import RuleSettings, {type RuleModel} from './RuleSettings.vue'

const props = defineProps<{
  initialData?: any
}>()

const formRef = ref<FormInstance>()

// 默认表单状态
const formData = reactive({
  event_name: '',
  weapon: '',
  gender: '',
  is_team_event: false,
  start_time: '',
  rules: {
    preset: 'world_cup',
    stages: []
  } as RuleModel
})

const formRules: FormRules = {
  event_name: [{required: true, message: '请输入项目名称', trigger: 'blur'}],
  weapon: [{required: true, message: '请选择剑种', trigger: 'change'}],
  gender: [{required: true, message: '请选择性别', trigger: 'change'}],
  start_time: [{required: true, message: '请选择时间', trigger: 'change'}]
}

// 监听初始数据变化（用于编辑模式）
watch(() => props.initialData, (newData) => {
  if (newData) {
    // 使用 Object.assign 确保响应式
    Object.assign(formData, JSON.parse(JSON.stringify(newData)))
  }
}, {immediate: true, deep: true})

// 暴露校验方法和数据给父组件
const validate = () => formRef.value?.validate()
defineExpose({formData, validate})
</script>
