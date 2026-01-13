<!-- src/components/tournament/RuleSettings.vue -->
<template>
  <div class="rule-settings-container">
    <!-- 1. 预设选择 -->
    <el-form-item label="赛制规则模板">
      <el-radio-group v-model="localPreset" @change="applyPreset">
        <el-radio-button label="world_cup">世界杯 (World Cup)</el-radio-button>
        <el-radio-button label="olympics">奥运会 (Olympics)</el-radio-button>
        <el-radio-button label="custom">自定义 (Custom)</el-radio-button>
      </el-radio-group>
    </el-form-item>

    <!-- 2. 阶段配置列表 -->
    <div class="stages-container">
      <transition-group name="list">
        <div v-for="(stage, index) in modelValue.stages" :key="index" class="stage-card">

          <!-- 阶段标题栏 -->
          <div class="stage-header">
            <div class="left">
              <el-tag :type="stage.type === 'pool' ? 'success' : 'danger'" effect="dark">
                阶段 {{ index + 1 }}: {{ stage.type === 'pool' ? '小组循环赛' : '单败淘汰赛' }}
              </el-tag>
            </div>
            <div class="right" v-if="localPreset === 'custom'">
              <el-button type="danger" link icon="Delete" @click="removeStage(index)"
                         :disabled="modelValue.stages.length <= 1">移除
              </el-button>
            </div>
          </div>

          <!-- 阶段配置表单 -->
          <div class="stage-body">
            <!-- A. 小组赛配置 -->
            <div v-if="stage.type === 'pool'" class="config-grid">
              <el-form-item label="轮空人数" class="mini-item">
                <el-input-number v-model="stage.config.byes" :min="0" size="small"/>
              </el-form-item>
              <el-form-item label="单场击中数" class="mini-item">
                <el-input-number v-model="stage.config.hits" :min="1" :max="15" size="small"/>
              </el-form-item>
              <el-form-item label="淘汰比例 (%)" class="mini-item">
                <el-input-number v-model="stage.config.elimination_rate" :min="0" :max="100" size="small"/>
              </el-form-item>
            </div>

            <!-- B. 淘汰赛配置 -->
            <div v-if="stage.type === 'de'" class="config-grid">
              <el-form-item label="单场击中数" class="mini-item">
                <el-input-number v-model="stage.config.hits" :min="1" :max="15" size="small"/>
              </el-form-item>
              <el-form-item label="决赛赛制" class="mini-item">
                <el-select v-model="stage.config.final_stage" size="small">
                  <el-option label="仅冠亚军" value="final"/>
                  <el-option label="含季军赛" value="bronze_medal"/>
                </el-select>
              </el-form-item>
              <el-form-item label="决出名次至" class="mini-item">
                <el-input-number v-model="stage.config.rank_to" :min="1" :max="64" size="small"/>
              </el-form-item>
            </div>
          </div>
        </div>
      </transition-group>

      <!-- 3. 自定义模式下的添加按钮 -->
      <div v-if="localPreset === 'custom'" class="add-stage-bar">
        <el-dropdown @command="addStage">
          <el-button type="primary" plain style="width: 100%">
            + 添加比赛阶段
            <el-icon class="el-icon--right">
              <ArrowDown/>
            </el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="pool">添加 小组循环赛 (Pool)</el-dropdown-item>
              <el-dropdown-item command="de">添加 单败淘汰赛 (DE)</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {ref, watch, onMounted} from 'vue'
import {ArrowDown, Delete} from '@element-plus/icons-vue'

// 定义规则的数据结构
export interface StageConfig {
  type: 'pool' | 'de';
  config: {
    byes?: number; // 轮空
    hits?: number; // 击中数
    elimination_rate?: number; // 淘汰率 (Pool)
    final_stage?: string; // 决赛类型 (DE)
    rank_to?: number; // 决出名次 (DE)
  }
}

export interface RuleModel {
  preset: string;
  stages: StageConfig[];
}

const props = defineProps<{ modelValue: RuleModel }>()
const emit = defineEmits(['update:modelValue'])

const localPreset = ref(props.modelValue.preset || 'world_cup')

// 预设模板生成器
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
  // 默认自定义初始状态
  return [
    {type: 'pool', config: {byes: 0, hits: 5, elimination_rate: 20}},
    {type: 'de', config: {hits: 15, final_stage: 'bronze_medal', rank_to: 4}}
  ];
}

const applyPreset = (val: string) => {
  if (val === 'custom') return; // 切换到自定义时不重置，保留当前状态或给默认

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

// 初始化检查
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
