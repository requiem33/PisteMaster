<!-- src/components/tournament/EditTournamentDrawer.vue -->
<template>
  <el-drawer
      :model-value="modelValue"
      title="编辑赛事信息"
      direction="rtl"
      size="40%"
      @update:model-value="$emit('update:modelValue', $event)"
  >
    <TournamentForm
        ref="tournamentFormRef"
        :initial-data="tournamentData"
        class="drawer-form"
    />
    <template #footer>
      <div class="drawer-footer">
        <el-button @click="$emit('update:modelValue', false)">取消</el-button>
        <el-button type="primary" :loading="isSubmitting" @click="submitForm">
          保存更新
        </el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import {ref} from 'vue'
import {DataManager} from '@/services/DataManager'
import {ElMessage} from 'element-plus'
import TournamentForm from './TournamentForm.vue'

const props = defineProps<{
  modelValue: boolean,
  tournamentData: any
}>()

const emit = defineEmits(['update:modelValue', 'success'])

const isSubmitting = ref(false)
const tournamentFormRef = ref<InstanceType<typeof TournamentForm>>()

const submitForm = async () => {
  if (!tournamentFormRef.value) return;

  // 【关键修改】4. 调用子组件的 validate
  const isValid = await tournamentFormRef.value.validate();
  if (isValid) {
    isSubmitting.value = true;
    try {
      // 【关键修改】5. 获取子组件的 formData
      await DataManager.updateTournament(tournamentFormRef.value.formData);
      ElMessage.success('赛事信息已更新');
      emit('success');
      emit('update:modelValue', false);
    } catch (error) {
      ElMessage.error('更新失败');
    } finally {
      isSubmitting.value = false;
    }
  }
}
</script>

<style scoped>
.drawer-form {
  padding: 0 20px;
}

.drawer-footer {
  text-align: right;
}
</style>
