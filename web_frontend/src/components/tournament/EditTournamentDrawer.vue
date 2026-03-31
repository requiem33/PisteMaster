<!-- src/components/tournament/EditTournamentDrawer.vue -->
<template>
  <el-drawer
      :model-value="modelValue"
      :title="$t('tournament.editDrawer.title')"
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
        <el-button @click="$emit('update:modelValue', false)">{{ $t('common.actions.cancel') }}</el-button>
        <el-button type="primary" :loading="isSubmitting" @click="submitForm">
          {{ $t('common.actions.save') }}
        </el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import {ref} from 'vue'
import {useI18n} from 'vue-i18n'
import {DataManager} from '@/services/DataManager'
import {ElMessage} from 'element-plus'
import TournamentForm from './TournamentForm.vue'

const {t} = useI18n()

defineProps<{
  modelValue: boolean,
  tournamentData: any
}>()

const emit = defineEmits(['update:modelValue', 'success'])

const isSubmitting = ref(false)
const tournamentFormRef = ref<InstanceType<typeof TournamentForm>>()

const submitForm = async () => {
  if (!tournamentFormRef.value) {return;}

  const isValid = await tournamentFormRef.value.validate();
  if (isValid) {
    isSubmitting.value = true;
    try {
      await DataManager.updateTournament(tournamentFormRef.value.formData);
      ElMessage.success(t('tournament.editDrawer.updateSuccess'));
      emit('success');
      emit('update:modelValue', false);
    } catch (_error) {
      ElMessage.error(t('tournament.editDrawer.updateFailed'));
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
