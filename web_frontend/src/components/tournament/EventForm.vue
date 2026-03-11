<template>
  <el-form :model="formData" :rules="formRules" ref="formRef" label-position="top">
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

    <el-divider content-position="left">赛制规则</el-divider>

    <el-form-item label="规则类型">
      <el-radio-group v-model="formData.rule_mode" @change="handleRuleModeChange">
        <el-radio-button label="preset">预设规则</el-radio-button>
        <el-radio-button label="custom">自定义规则</el-radio-button>
      </el-radio-group>
    </el-form-item>

    <el-form-item v-if="formData.rule_mode === 'preset'" label="选择规则">
      <el-select 
          v-model="formData.rule_id" 
          placeholder="请选择预设规则" 
          style="width: 100%"
          :loading="loadingRules"
      >
        <el-option 
            v-for="rule in presetRules" 
            :key="rule.id" 
            :label="rule.rule_name" 
            :value="rule.id"
        >
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>{{ rule.rule_name }}</span>
            <el-tag size="small" type="info">{{ rule.stages_config?.length || 0 }} 阶段</el-tag>
          </div>
        </el-option>
      </el-select>

      <div v-if="selectedRule" class="rule-preview">
        <p class="preview-label">阶段配置：</p>
        <div class="stages-preview">
          <el-tag 
              v-for="(stage, idx) in selectedRule.stages_config" 
              :key="idx"
              :type="stage.type === 'pool' ? 'success' : 'danger'"
              effect="light"
              class="stage-tag"
          >
            阶段{{ idx + 1 }}: {{ stage.type === 'pool' ? '小组赛' : '淘汰赛' }}
          </el-tag>
        </div>
        <p class="preview-desc">{{ selectedRule.description }}</p>
      </div>
    </el-form-item>

    <RuleSettings 
        v-if="formData.rule_mode === 'custom'" 
        v-model="formData.rules" 
    />
  </el-form>
</template>

<script setup lang="ts">
import {ref, reactive, watch, computed, onMounted} from 'vue'
import type {FormInstance, FormRules} from 'element-plus'
import {DataManager} from '@/services/DataManager'
import RuleSettings, {type RuleModel} from './RuleSettings.vue'

const props = defineProps<{
  initialData?: any
}>()

const formRef = ref<FormInstance>()
const presetRules = ref<any[]>([])
const loadingRules = ref(false)

const formData = reactive({
  event_name: '',
  weapon: '',
  gender: '',
  is_team_event: false,
  start_time: '',
  rule_mode: 'preset' as 'preset' | 'custom',
  rule_id: null as string | null,
  rules: {
    preset: 'custom',
    stages: []
  } as RuleModel
})

const formRules: FormRules = {
  event_name: [{required: true, message: '请输入项目名称', trigger: 'blur'}],
  weapon: [{required: true, message: '请选择剑种', trigger: 'change'}],
  gender: [{required: true, message: '请选择性别', trigger: 'change'}],
  start_time: [{required: true, message: '请选择时间', trigger: 'change'}]
}

const selectedRule = computed(() => 
    presetRules.value.find(r => r.id === formData.rule_id)
)

const loadPresetRules = async () => {
  loadingRules.value = true
  try {
    presetRules.value = await DataManager.fetchRules()
    if (presetRules.value.length > 0 && !formData.rule_id) {
      formData.rule_id = presetRules.value[0].id
    }
  } catch (error) {
    console.error('Failed to load preset rules:', error)
  } finally {
    loadingRules.value = false
  }
}

const handleRuleModeChange = (mode: 'preset' | 'custom') => {
  if (mode === 'preset') {
    const preset = presetRules.value.find(r => r.is_preset)
    if (preset) {
      formData.rule_id = preset.id
    }
  } else {
    formData.rule_id = null
  }
}

onMounted(() => {
  loadPresetRules()
})

watch(() => props.initialData, (newData) => {
  if (newData) {
    Object.assign(formData, JSON.parse(JSON.stringify(newData)))
    if (newData.rule_info) {
      if (newData.rule_info.is_custom) {
        formData.rule_mode = 'custom'
        formData.rules = {
          preset: 'custom',
          stages: newData.rule_info.stages || []
        }
      } else if (newData.rule_info.id) {
        formData.rule_mode = 'preset'
        formData.rule_id = newData.rule_info.id
      }
    }
  }
}, {immediate: true, deep: true})

const validate = () => formRef.value?.validate()
defineExpose({formData, validate})
</script>

<style scoped lang="scss">
.rule-preview {
  margin-top: 12px;
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 6px;
}

.preview-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}

.stages-preview {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.stage-tag {
  font-size: 12px;
}

.preview-desc {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 8px;
  margin-bottom: 0;
}
</style>
