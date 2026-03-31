<!-- src/components/tournament/FencerImport.vue -->
<template>
  <div class="fencer-import-container">
    <div class="action-bar">
      <div class="left">
        <el-button type="primary" icon="Plus" @click="addRow">{{ $t('event.fencer.addRow') }}</el-button>
        <el-button type="success" icon="Memo" @click="showPasteArea = !showPasteArea">
          {{ showPasteArea ? $t('event.fencer.closePaste') : $t('event.fencer.pasteFromExcel') }}
        </el-button>
      </div>
      <div class="right">
        <el-button type="danger" plain icon="Delete" @click="clearAll" :disabled="!fencers.length">
          {{ $t('event.fencer.clearAll') }}
        </el-button>
      </div>
    </div>

    <el-collapse-transition>
      <div v-if="showPasteArea" class="paste-area">
        <el-input
            v-model="rawPasteData"
            type="textarea"
            :rows="8"
            :placeholder="$t('event.fencer.pasteHint')"
        />
        <div class="paste-actions">
          <el-button type="primary" @click="parseAndImport" :loading="isParsing">{{ $t('event.fencer.parseAndImport') }}</el-button>
          <span class="hint">{{ $t('event.fencer.parseHint') }}</span>
        </div>
      </div>
    </el-collapse-transition>

    <el-table :data="fencers" border stripe class="fencer-table">
      <el-table-column type="index" :label="$t('event.fencer.index')" width="60" align="center"/>
      <el-table-column :label="$t('event.fencer.lastName')">
        <template #default="scope">
          <el-input v-model="scope.row.last_name" :placeholder="$t('event.fencer.required')"/>
        </template>
      </el-table-column>
      <el-table-column :label="$t('event.fencer.firstName')">
        <template #default="scope">
          <el-input v-model="scope.row.first_name" :placeholder="$t('event.fencer.required')"/>
        </template>
      </el-table-column>
      <el-table-column :label="$t('event.fencer.gender')" width="100">
        <template #default="scope">
          <el-select v-model="scope.row.gender">
            <el-option :label="$t('event.fencer.male')" value="M"/>
            <el-option :label="$t('event.fencer.female')" value="F"/>
          </el-select>
        </template>
      </el-table-column>
      <el-table-column :label="$t('event.fencer.country')" width="120">
        <template #default="scope">
          <el-input v-model="scope.row.country_code" :placeholder="$t('event.fencer.countryPlaceholder')" maxlength="3"/>
        </template>
      </el-table-column>
      <el-table-column :label="$t('event.fencer.initialRanking')" width="120">
        <template #default="scope">
          <el-input-number v-model="scope.row.current_ranking" :min="0" controls-position="right" style="width: 100%"/>
        </template>
      </el-table-column>
      <el-table-column :label="$t('event.fencer.actions')" width="70" align="center">
        <template #default="scope">
          <el-button type="danger" icon="Delete" circle @click="removeRow(scope.$index)"/>
        </template>
      </el-table-column>
    </el-table>

    <footer class="import-footer">
      <div class="info">
        {{ $t('event.pool.fencersReady', {n: fencers.length}) }}
      </div>
      <el-button type="primary" size="large" icon="Check" :loading="isSubmitting" @click="submitImport">
        {{ $t('event.pool.saveListAndNext') }}
      </el-button>
    </footer>
  </div>
</template>

<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {useI18n} from 'vue-i18n'
import {ElMessage, ElMessageBox} from 'element-plus'
import {DataManager} from '@/services/DataManager'

const {t} = useI18n()

const props = defineProps<{
  eventId: string
}>()
const emit = defineEmits(['next'])

interface FencerRow {
  id?: string
  last_name: string
  first_name: string
  gender: string
  country_code: string
  current_ranking: number | null
  fencing_id?: string
}

const fencers = ref<FencerRow[]>([])
const showPasteArea = ref(false)
const rawPasteData = ref('')
const isSubmitting = ref(false)
const isParsing = ref(false)

const addRow = () => {
  fencers.value.unshift({
    last_name: '',
    first_name: '',
    gender: 'M',
    country_code: 'CHN',
    current_ranking: 999
  })
}

const removeRow = (index: number) => {
  fencers.value.splice(index, 1)
}

const clearAll = () => {
  ElMessageBox.confirm(t('common.confirm.deleteTitle'), t('common.actions.confirm'), {type: 'warning'})
      .then(() => {
        fencers.value = []
      })
}

const parseAndImport = () => {
  if (!rawPasteData.value.trim()) {return;}
  isParsing.value = true;
  try {
    const lines = rawPasteData.value.trim().split('\n');
    const newFencers: FencerRow[] = [];
    lines.forEach(line => {
      if (!line.trim()) {return;}
      const columns = line.split(/\t| {2,}/).map(col => col.trim());
      const lastName = columns[0] || '';
      const firstName = columns[1] || '';
      const genderRaw = (columns.find(c => c.toUpperCase() === 'F' || c === '女' || c === 'Female') || 'M').toUpperCase();
      const gender = genderRaw.startsWith('F') ? 'F' : 'M';
      const countryCodeRaw = columns.find(c => /^[A-Z]{3}$/.test(c));
      const country_code = countryCodeRaw || 'CHN';
      let ranking: number | null = 999;
      const rankingStr = columns.find(c => /^\d+$/.test(c) && c.length < 4);
      if (rankingStr) {ranking = parseInt(rankingStr, 10);}

      if (lastName && firstName) {
        newFencers.push({last_name: lastName, first_name: firstName, gender, country_code, current_ranking: ranking});
      }
    });
    if (newFencers.length > 0) {
      fencers.value = [...fencers.value, ...newFencers];
      ElMessage.success(t('event.pool.parseSuccess', {n: newFencers.length}));
      rawPasteData.value = '';
      showPasteArea.value = false;
    } else {
      ElMessage.error(t('event.pool.parseFailed'));
    }
  } finally {
    isParsing.value = false;
  }
};

const submitImport = async () => {
  const invalidFencer = fencers.value.find(f => !f.last_name || !f.first_name);
  if (invalidFencer) {
    ElMessage.error(t('event.pool.missingNameError'));
    return;
  }

  isSubmitting.value = true;
  try {
    const savedFencers = await DataManager.saveFencers(fencers.value);
    const currentIds = savedFencers.map((f: any) => f.id);
    await DataManager.syncEventFencers(props.eventId, currentIds);

    await DataManager.initializeLiveRanking(props.eventId, savedFencers);

    ElMessage.success(t('event.pool.listSaved'));
    emit('next');
  } catch (error) {
    console.error(error);
    ElMessage.error(t('event.pool.saveFailed'));
  } finally {
    isSubmitting.value = false;
  }
};

const loadExistingFencers = async (): Promise<void> => {
  try {
    const data = await DataManager.getFencersByEvent(props.eventId)
    fencers.value = data.map((f: FencerRow) => ({
      id: f.id,
      last_name: f.last_name,
      first_name: f.first_name,
      gender: f.gender || 'M',
      country_code: f.country_code || 'CHN',
      current_ranking: f.current_ranking,
      fencing_id: f.fencing_id
    }))
  } catch (error) {
    console.error('加载选手失败:', error)
  }
}

onMounted(() => {
  if (props.eventId) {
    loadExistingFencers()
  }
})
</script>

<style scoped lang="scss">
/* 样式部分保持不变 */
.fencer-import-container {
  padding: 10px;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.paste-area {
  background: var(--el-fill-color-light);
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  border: 1px dashed var(--el-border-color-darker);

  .paste-actions {
    margin-top: 15px;
    display: flex;
    align-items: center;
    gap: 20px;

    .hint {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }
  }
}

.fencer-table {
  margin-top: 20px;

  :deep(.el-input__inner) {
    text-align: left;
  }
}

.import-footer {
  margin-top: 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-top: 1px solid var(--el-border-color-lighter);

  .info {
    font-size: 16px;

    .count {
      font-weight: bold;
      color: var(--el-color-primary);
      font-size: 24px;
      margin: 0 5px;
    }
  }
}
</style>
