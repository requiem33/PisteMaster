<!-- src/components/tournament/RuleSettings.vue -->
<template>
  <div class="rule-settings-container">
    <el-form-item :label="$t('event.ruleSettings.template')">
      <el-radio-group v-model="localPreset" @change="applyPreset">
        <el-radio-button label="world_cup">{{ $t('event.ruleSettings.worldCup') }} (World Cup)</el-radio-button>
        <el-radio-button label="olympics">{{ $t('event.ruleSettings.olympics') }} (Olympics)</el-radio-button>
        <el-radio-button label="custom">{{ $t('event.ruleSettings.custom') }} (Custom)</el-radio-button>
      </el-radio-group>
    </el-form-item>

    <div class="stages-container">
      <transition-group name="list">
        <div v-for="(stage, index) in modelValue.stages" :key="index" class="stage-card">

          <div class="stage-header">
            <div class="left">
              <el-tag :type="stage.type === 'pool' ? 'success' : 'danger'" effect="dark">
                {{ $t('event.ruleSettings.stageN', {n: index + 1}) }}: {{ stage.type === 'pool' ? $t('event.ruleSettings.poolStage') : $t('event.ruleSettings.deStage') }}
              </el-tag>
            </div>
            <div class="right" v-if="localPreset === 'custom'">
              <el-button type="danger" link icon="Delete" @click="removeStage(index)"
                         :disabled="modelValue.stages.length <= 1">{{ $t('event.ruleSettings.removeStage') }}
              </el-button>
            </div>
          </div>

          <div class="stage-body">
            <div v-if="stage.type === 'pool'" class="config-grid">
              <el-form-item :label="$t('event.ruleSettings.byes')" class="mini-item">
                <el-input-number v-model="stage.config.byes" :min="0" size="small"/>
              </el-form-item>
              <el-form-item :label="$t('event.ruleSettings.hits')" class="mini-item">
                <el-input-number v-model="stage.config.hits" :min="1" :max="15" size="small"/>
              </el-form-item>
              <el-form-item :label="$t('event.ruleSettings.eliminationRate')" class="mini-item">
                <el-input-number v-model="stage.config.elimination_rate" :min="0" :max="100" size="small"/>
              </el-form-item>
            </div>

            <div v-if="stage.type === 'de'" class="config-grid">
              <el-form-item :label="$t('event.ruleSettings.hits')" class="mini-item">
                <el-input-number v-model="stage.config.hits" :min="1" :max="15" size="small"/>
              </el-form-item>
              <el-form-item :label="$t('event.ruleSettings.finalStage')" class="mini-item">
                <el-select v-model="stage.config.final_stage" size="small">
                  <el-option :label="$t('event.ruleSettings.finalOnly')" value="final"/>
                  <el-option :label="$t('event.ruleSettings.bronzeMedal')" value="bronze_medal"/>
                </el-select>
              </el-form-item>
              <el-form-item :label="$t('event.ruleSettings.rankTo')" class="mini-item">
                <el-input-number v-model="stage.config.rank_to" :min="1" :max="64" size="small"/>
              </el-form-item>
            </div>
          </div>
        </div>
      </transition-group>

      <div v-if="localPreset === 'custom'" class="add-stage-bar">
        <el-dropdown @command="addStage">
          <el-button type="primary" plain style="width: 100%">
            + {{ $t('event.ruleSettings.addStage') }}
            <el-icon class="el-icon--right">
              <ArrowDown/>
            </el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="pool">{{ $t('event.ruleSettings.addPool') }}</el-dropdown-item>
              <el-dropdown-item command="de">{{ $t('event.ruleSettings.addDE') }}</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {ref, onMounted} from 'vue'
import {ArrowDown} from '@element-plus/icons-vue'

export interface StageConfig {
  type: 'pool' | 'de';
  config: {
    byes?: number;
    hits?: number;
    elimination_rate?: number;
    final_stage?: string;
    rank_to?: number;
  }
}

export interface RuleModel {
  preset: string;
  stages: StageConfig[];
}

const props = defineProps<{ modelValue: RuleModel }>()
const emit = defineEmits(['update:modelValue'])

const localPreset = ref(props.modelValue.preset || 'world_cup')

const getTemplate = (type: string): StageConfig[] => {
  if (type === 'world_cup') {
    return [
      {type: 'pool', config: {byes: 16, hits: 5, elimination_rate: 20}},
      {type: 'de', config: {hits: 15, final_stage: 'bronze_medal', rank_to: 8}}
    ];
  }
  if (type === 'olympics') {
    return [
      {type: 'de', config: {hits: 15, final_stage: 'bronze_medal', rank_to: 8}}
    ];
  }
  return [
    {type: 'pool', config: {byes: 0, hits: 5, elimination_rate: 20}},
    {type: 'de', config: {hits: 15, final_stage: 'bronze_medal', rank_to: 4}}
  ];
}

const applyPreset = (val: string) => {
  if (val === 'custom') {return;}

  const newStages = getTemplate(val);
  emit('update:modelValue', {preset: val, stages: newStages});
}

const addStage = (type: 'pool' | 'de') => {
  const newStage: StageConfig = type === 'pool'
      ? {type: 'pool', config: {byes: 0, hits: 5, elimination_rate: 20}}
      : {type: 'de', config: {hits: 15, final_stage: 'final', rank_to: 4}};

  const newStages = [...props.modelValue.stages, newStage];
  emit('update:modelValue', {preset: 'custom', stages: newStages});
}

const removeStage = (index: number) => {
  const newStages = [...props.modelValue.stages];
  newStages.splice(index, 1);
  emit('update:modelValue', {preset: 'custom', stages: newStages});
}

onMounted(() => {
  if (!props.modelValue.stages || props.modelValue.stages.length === 0) {
    applyPreset('world_cup');
  }
})
</script>

<style scoped lang="scss">
.rule-settings-container {
  border: 1px solid var(--el-border-color-lighter);
  padding: 15px;
  border-radius: 8px;
  background: var(--el-fill-color-blank);
}

.stages-container {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.stage-card {
  border: 1px solid var(--el-border-color-light);
  border-radius: 6px;
  background: #fff;
  overflow: hidden;
  transition: all 0.3s;

  .stage-header {
    padding: 8px 15px;
    background: var(--el-fill-color-light);
    border-bottom: 1px solid var(--el-border-color-light);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .stage-body {
    padding: 15px;
  }
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;

  .mini-item {
    margin-bottom: 0;

    :deep(.el-form-item__label) {
      font-size: 12px;
      line-height: 1.5;
      padding-bottom: 4px;
    }
  }
}

.add-stage-bar {
  text-align: center;
  margin-top: 10px;
  border-top: 1px dashed var(--el-border-color);
  padding-top: 15px;
}

/* 列表动画 */
.list-enter-active, .list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from, .list-leave-to {
  opacity: 0;
  transform: translateY(30px);
}
</style>
