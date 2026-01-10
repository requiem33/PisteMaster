<template>
  <div class="de-tree-container">
    <div class="tree-controls">
      <el-radio-group v-model="viewBracket" size="small">
        <el-radio-button label="64">Table of 64</el-radio-button>
        <el-radio-button label="32">Table of 32</el-radio-button>
        <el-radio-button label="16">Table of 16</el-radio-button>
      </el-radio-group>
      <el-button type="primary" icon="Printer" plain>打印对阵表</el-button>
    </div>

    <div v-loading="loading" class="bracket-viewport" ref="viewportRef">
      <svg class="connection-layer">
        <path
            v-for="(line, idx) in connections"
            :key="idx"
            :d="line.d"
            class="connection-line"
            :class="{ 'bye-connection': line.isBye }"
        />
      </svg>

      <div v-for="(round, rIdx) in bracketData" :key="rIdx" class="round-column">
        <div class="round-header">Table of {{ Math.pow(2, bracketData.length - rIdx) }}</div>
        <div class="matches-container">
          <div
              v-for="(match, mIdx) in round"
              :key="match.id"
              class="match-wrapper"
              :ref="el => setMatchRef(el as HTMLElement, rIdx, mIdx)"
          >
            <div class="match-box" :class="{ 'has-winner': !!match.winnerId }">
              <div class="fencer-slot" :class="getSlotClass(match, 'A')">
                <template v-if="match.fencerA">
                  <span class="seed">{{ match.fencerA.seed }}</span>
                  <div class="fencer-info">
                    <span class="name"><span class="ln">{{ match.fencerA.last_name }}</span> {{
                        match.fencerA.first_name
                      }}</span>
                    <span class="org">{{ match.fencerA.country_code }}</span>
                  </div>
                  <input
                      v-model="match.scoreA"
                      class="score-input"
                      :disabled="!match.fencerB"
                      @change="handleScoreChange(rIdx, mIdx)"
                  />
                </template>
                <span v-else class="name bye-text">BYE</span>
              </div>
              <div class="divider"></div>
              <div class="fencer-slot" :class="getSlotClass(match, 'B')">
                <template v-if="match.fencerB">
                  <span class="seed">{{ match.fencerB.seed }}</span>
                  <div class="fencer-info">
                    <span class="name"><span class="ln">{{ match.fencerB.last_name }}</span> {{
                        match.fencerB.first_name
                      }}</span>
                    <span class="org">{{ match.fencerB.country_code }}</span>
                  </div>
                  <input
                      v-model="match.scoreB"
                      class="score-input"
                      :disabled="!match.fencerA"
                      @change="handleScoreChange(rIdx, mIdx)"
                  />
                </template>
                <span v-else class="name bye-text">BYE</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {ref, onMounted, onUnmounted, nextTick} from 'vue'
import {DataManager} from '@/services/DataManager'
import {ElMessage} from 'element-plus'

// --- 类型定义 ---
interface Fencer {
  id: string | number // 兼容数字ID
  last_name: string
  first_name: string
  country_code: string
  seed: number
}

interface Match {
  id: number
  fencerA: Fencer | null
  fencerB: Fencer | null
  scoreA: number | string
  scoreB: number | string
  winnerId: string | null // 统一存储为字符串以保证比较安全
}

interface Connection {
  d: string
  isBye: boolean
}

// --- 状态与引用 ---
const props = defineProps<{ eventId: string }>()
const viewBracket = ref('16')
const bracketData = ref<Match[][]>([])
const connections = ref<Connection[]>([])
const loading = ref(false)
const viewportRef = ref<HTMLElement>()
const matchRefs = new Map<string, HTMLElement>()
let resizeObserver: ResizeObserver | null = null

// --- 核心交互逻辑 (修复部分) ---

// 辅助：安全获取 ID 字符串
const getSafeId = (fencer: Fencer | null): string | null => {
  return fencer && fencer.id !== undefined && fencer.id !== null ? String(fencer.id) : null;
}

// 辅助：解析分数为数字，支持 "V"
const parseScore = (val: string | number): number => {
  if (val === null || val === undefined) return -1;
  const strVal = String(val).trim().toUpperCase();
  if (strVal === '') return -1;
  if (strVal === 'V') return 999; // V 视为最大值
  // 处理 "V5" 这种情况，如果包含 V，提取后面的数字并加上权重，或者简单处理
  if (strVal.startsWith('V')) {
    const numPart = parseInt(strVal.replace('V', ''));
    return isNaN(numPart) ? 999 : 100 + numPart; // V5 > 5
  }
  const num = Number(val);
  return isNaN(num) ? -1 : num;
}

/**
 * 计算并更新单场比赛的胜者
 */
const updateMatchWinner = (rIdx: number, mIdx: number) => {
  const match = bracketData.value[rIdx][mIdx];

  // 获取 ID
  const idA = getSafeId(match.fencerA);
  const idB = getSafeId(match.fencerB);

  // 如果有一方是轮空 (BYE)，另一方自动获胜
  if (match.fencerA && !match.fencerB) {
    match.winnerId = idA;
    return;
  }
  if (!match.fencerA && match.fencerB) {
    match.winnerId = idB;
    return;
  }

  // 双方都在，比较分数
  const sA = parseScore(match.scoreA);
  const sB = parseScore(match.scoreB);

  // 只有当两个分数都有效输入时才判断胜负
  if (sA !== -1 && sB !== -1) {
    if (sA > sB) match.winnerId = idA;
    else if (sB > sA) match.winnerId = idB;
    else match.winnerId = null; // 平局或未完成
  } else {
    // 分数不完整，重置胜者
    match.winnerId = null;
  }
};


/**
 * 核心：处理比分变更，并触发连锁更新
 */
const handleScoreChange = (rIdx: number, mIdx: number) => {
  // 1. 更新当前比赛胜者
  updateMatchWinner(rIdx, mIdx);

  // 2. 连锁更新后续轮次
  for (let currentRIdx = rIdx; currentRIdx < bracketData.value.length - 1; currentRIdx++) {
    // 当前循环处理的比赛索引
    const currentMIdxInLoop = Math.floor(mIdx / Math.pow(2, currentRIdx - rIdx));
    const currentMatch = bracketData.value[currentRIdx][currentMIdxInLoop];

    // 获取当前决出的胜者对象
    let winner: Fencer | null = null;
    const wId = currentMatch.winnerId;

    if (wId) {
      if (getSafeId(currentMatch.fencerA) === wId) winner = currentMatch.fencerA;
      else if (getSafeId(currentMatch.fencerB) === wId) winner = currentMatch.fencerB;
    }

    // 定位下一轮的比赛
    const nextRIdx = currentRIdx + 1;
    const nextMIdx = Math.floor(currentMIdxInLoop / 2);

    // 边界检查
    if (!bracketData.value[nextRIdx] || !bracketData.value[nextRIdx][nextMIdx]) break;

    const nextMatch = bracketData.value[nextRIdx][nextMIdx];

    // 检查是否有变更
    let participantChanged = false;
    const isSourceA = (currentMIdxInLoop % 2 === 0);

    if (isSourceA) {
      // 下一轮的 A 选手位置
      if (getSafeId(nextMatch.fencerA) !== getSafeId(winner)) {
        nextMatch.fencerA = winner;
        participantChanged = true;
      }
    } else {
      // 下一轮的 B 选手位置
      if (getSafeId(nextMatch.fencerB) !== getSafeId(winner)) {
        nextMatch.fencerB = winner;
        participantChanged = true;
      }
    }

    // 如果参赛者变了，清空下一轮的比分并重新计算其胜者（通常会变成 null）
    if (participantChanged) {
      nextMatch.scoreA = '';
      nextMatch.scoreB = '';
      updateMatchWinner(nextRIdx, nextMIdx);
    }

    // 如果没有变更，且下一轮也没有胜者，通常不需要继续深层递归，但为了安全继续循环
  }

  // 3. 保存并重绘
  saveProgress();
  // 强制 Vue 更新视图后再画线
  nextTick(() => {
    drawLines();
  });
};

// --- 数据持久化 ---
const saveProgress = async () => {
  await DataManager.saveDETree(props.eventId, bracketData.value);
};

// --- 初始化与数据加载 ---
const getSeedOrder = (size: number): number[] => {
  let order = [1];
  while (order.length < size) {
    const nextOrder = [];
    const currentMax = order.length * 2;
    for (const s of order) {
      nextOrder.push(s);
      nextOrder.push(currentMax + 1 - s);
    }
    order = nextOrder;
  }
  return order;
};

const initRealDE = async () => {
  loading.value = true;
  try {
    const savedTree = await DataManager.getDETree(props.eventId);
    if (savedTree && savedTree.length > 0) {
      bracketData.value = savedTree;
      nextTick(drawLines);
      ElMessage.success('已恢复上次保存的对阵图进度');
      return;
    }
    const qualifiedFencers = await DataManager.getQualifiedFencersForDE(props.eventId);
    if (qualifiedFencers.length === 0) {
      ElMessage.warning('暂无晋级选手数据');
      return;
    }
    const count = qualifiedFencers.length;
    const bracketSize = Math.pow(2, Math.ceil(Math.log2(count)));
    viewBracket.value = bracketSize.toString();
    const seedOrder = getSeedOrder(bracketSize);

    const firstRound: Match[] = [];
    const fencerMap = new Map(qualifiedFencers.map(f => [f.seed, f]));

    for (let i = 0; i < seedOrder.length; i += 2) {
      const fencerA = fencerMap.get(seedOrder[i]) || null;
      const fencerB = fencerMap.get(seedOrder[i + 1]) || null;

      const match: Match = {
        id: i / 2 + 1,
        fencerA,
        fencerB,
        scoreA: '',
        scoreB: '',
        winnerId: null
      };

      // 自动处理首轮轮空
      if (fencerA && !fencerB) {
        match.winnerId = getSafeId(fencerA);
        match.scoreA = 'V';
      }
      firstRound.push(match);
    }

    const allRounds = [firstRound];
    let currentSize = firstRound.length / 2;
    while (currentSize >= 1) {
      allRounds.push(Array.from({length: currentSize}, (_, idx) => ({
        id: Math.random(), // 临时 ID，仅用于 Key
        fencerA: null,
        fencerB: null,
        scoreA: '',
        scoreB: '',
        winnerId: null
      })));
      currentSize /= 2;
    }
    bracketData.value = allRounds;

    // 重新运行一次分数检查，确保初始化的 'V' 被正确识别
    nextTick(() => {
      firstRound.forEach((m, idx) => {
        if (m.winnerId) {
          handleScoreChange(0, idx);
        }
      });
      drawLines();
    });

  } catch (error) {
    console.error(error);
    ElMessage.error('初始化对阵表失败');
  } finally {
    loading.value = false;
  }
};

// --- 绘图与辅助函数 ---

// 修复：使用 String 强转 ID 进行比较，避免数字/字符串不匹配
const getSlotClass = (match: Match, side: 'A' | 'B') => {
  const fencer = side === 'A' ? match.fencerA : match.fencerB;
  // 核心修复点：将两边都转为 String 再比较
  const isWinner = match.winnerId && fencer && String(match.winnerId) === String(fencer.id);
  return {'winner': isWinner, 'bye-slot': !fencer};
};

const setMatchRef = (el: HTMLElement | null, rIdx: number, mIdx: number) => {
  if (el) matchRefs.set(`${rIdx}-${mIdx}`, el);
};

const drawLines = () => {
  if (!viewportRef.value) return;
  const newConnections: Connection[] = [];
  const viewportRect = viewportRef.value.getBoundingClientRect();
  for (let r = 0; r < bracketData.value.length - 1; r++) {
    for (let m = 0; m < bracketData.value[r].length; m++) {
      const currEl = matchRefs.get(`${r}-${m}`);
      const nextEl = matchRefs.get(`${r + 1}-${Math.floor(m / 2)}`);
      if (!currEl || !nextEl) continue;

      const startRect = currEl.getBoundingClientRect();
      const endRect = nextEl.getBoundingClientRect();

      const startX = startRect.right - viewportRect.left;
      const startY = startRect.top + startRect.height / 2 - viewportRect.top;
      const endX = endRect.left - viewportRect.left;
      const endY = endRect.top + endRect.height / 2 - viewportRect.top;

      const midX = startX + (endX - startX) / 2;
      const d = `M ${startX} ${startY} H ${midX} V ${endY} H ${endX}`;

      const isBye = !bracketData.value[r][m].fencerA || !bracketData.value[r][m].fencerB;
      newConnections.push({d, isBye});
    }
  }
  connections.value = newConnections;
};

// --- 生命周期 ---
onMounted(() => {
  initRealDE();
  if (viewportRef.value) {
    resizeObserver = new ResizeObserver(() => requestAnimationFrame(drawLines));
    resizeObserver.observe(viewportRef.value);
  }
});
onUnmounted(() => {
  resizeObserver?.disconnect();
});
</script>

<style scoped lang="scss">
/* 样式保持不变 */
$border-color: #dcdfe6;
$winner-color: #67c23a;
$bg-color: #f8f9fa;
@mixin text-ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.de-tree-container {
  background: $bg-color;
  padding: 20px;
  min-height: 600px;
  position: relative;
}

.tree-controls {
  margin-bottom: 30px;
  display: flex;
  justify-content: space-between;
}

.bracket-viewport {
  display: flex;
  gap: 80px;
  padding: 40px 20px;
  position: relative;
  overflow-x: auto;
  min-height: 600px;
}

.connection-layer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.connection-line {
  fill: none;
  stroke: $border-color;
  stroke-width: 2;

  &.bye-connection {
    stroke-dasharray: 5, 5;
    opacity: 0.7;
  }
}

.round-column {
  display: flex;
  flex-direction: column;
  min-width: 280px;
  z-index: 2;

  .round-header {
    text-align: center;
    font-weight: bold;
    color: #909399;
    margin-bottom: 20px;
    font-size: 12px;
    text-transform: uppercase;
  }
}

.matches-container {
  display: flex;
  flex-direction: column;
  justify-content: space-around;
  flex-grow: 1;
}

.match-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  position: relative;
  padding: 5px 0;
}

.match-box {
  flex-grow: 1;
  background: white;
  border: 1px solid $border-color;
  border-radius: 4px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  overflow: hidden;
  transition: all 0.2s;

  &.has-winner {
    border-color: $winner-color;
  }
}

.fencer-slot {
  display: flex;
  align-items: center;
  height: 38px;
  padding: 0 0 0 10px;
  font-size: 13px;

  &.winner {
    background: #f0f9eb;
    font-weight: bold;

    .name, .seed, .org {
      color: #529b2e;
    }
  }

  &.bye-slot {
    background: #fafafa;
    color: #c0c4cc;
    font-style: italic;
  }

  .seed {
    width: 24px;
    color: #999;
    font-size: 11px;
  }

  .fencer-info {
    flex: 1;
    display: flex;
    justify-content: space-between;
    align-items: center;
    overflow: hidden;
    margin-right: 8px;
  }

  .name {
    @include text-ellipsis;

    .ln {
      text-transform: uppercase;
      font-weight: bold;
    }
  }

  .org {
    font-size: 10px;
    color: #909399;
    background: #f0f2f5;
    padding: 1px 4px;
    border-radius: 3px;
    margin-left: 5px;
    flex-shrink: 0;
  }

  .score-input {
    width: 35px;
    height: 100%;
    border: none;
    border-left: 1px solid #f0f0f0;
    text-align: center;
    font-weight: bold;
    background: transparent;
    outline: none;

    &:focus {
      background: #e6f7ff;
    }

    &:disabled {
      background: #fafafa;
      cursor: not-allowed;
      color: #c0c4cc;
    }
  }
}

.divider {
  height: 1px;
  background: #f0f0f0;
}

</style>