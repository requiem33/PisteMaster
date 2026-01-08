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

    <div class="bracket-viewport" ref="viewportRef">
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
                    <span class="name">
                      <span class="ln">{{ match.fencerA.last_name }}</span>
                      {{ match.fencerA.first_name }}
                    </span>
                    <span class="org">{{ match.fencerA.country_code }}</span>
                  </div>
                  <input
                      v-model.number="match.scoreA"
                      class="score-input"
                      @input="handleScoreChange(rIdx, mIdx)"
                  />
                </template>
                <span v-else class="name bye-text">BYE</span>
              </div>

              <div class="divider"></div>

              <div class="fencer-slot" :class="getSlotClass(match, 'B')">
                <template v-if="match.fencerB">
                  <span class="seed">{{ match.fencerB.seed }}</span>
                  <div class="fencer-info">
                    <span class="name">
                      <span class="ln">{{ match.fencerB.last_name }}</span>
                      {{ match.fencerB.first_name }}
                    </span>
                    <span class="org">{{ match.fencerB.country_code }}</span>
                  </div>
                  <input
                      v-model.number="match.scoreB"
                      class="score-input"
                      @input="handleScoreChange(rIdx, mIdx)"
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
  id: string
  last_name: string
  first_name: string    // 👈 新增
  country_code: string  // 👈 新增
  seed: number
}

interface Match {
  id: number
  fencerA: Fencer | null
  fencerB: Fencer | null
  scoreA: number | string
  scoreB: number | string
  winnerId: string | null
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

// --- 核心算法：生成标准对阵种子序列 ---
// 例如 size=8, 返回 [1, 8, 5, 4, 3, 6, 7, 2]
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

// --- 初始化真实 DE 数据 ---
const initRealDE = async () => {
  loading.value = true;
  try {
    // 1. 获取晋级名单
    const qualifiedFencers = await DataManager.getQualifiedFencersForDE(props.eventId);
    if (qualifiedFencers.length === 0) {
      ElMessage.warning('暂无晋级选手数据，请先完成小组赛计分');
      return;
    }

    // 2. 确定对阵表规模 (16强, 32强, 64强...)
    // 根据选手人数自动计算最小的 2 的幂
    const count = qualifiedFencers.length;
    const bracketSize = Math.pow(2, Math.ceil(Math.log2(count)));
    viewBracket.value = bracketSize.toString();

    // 3. 生成第一轮对阵 (Table of X)
    const seedOrder = getSeedOrder(bracketSize);
    const firstRound: Match[] = [];
    const fencerMap = new Map(qualifiedFencers.map(f => [f.seed, f]));

    for (let i = 0; i < seedOrder.length; i += 2) {
      const seedA = seedOrder[i];
      const seedB = seedOrder[i + 1];
      const fencerA = fencerMap.get(seedA) || null;
      const fencerB = fencerMap.get(seedB) || null;

      const match: Match = {
        id: i / 2 + 1,
        fencerA: fencerA,
        fencerB: fencerB,
        scoreA: '',
        scoreB: '',
        winnerId: null
      };

      // 自动处理轮空 (Bye)
      if (fencerA && !fencerB) {
        match.winnerId = fencerA.id;
        match.scoreA = 'V';
        match.scoreB = '0';
      } else if (!fencerA && fencerB) {
        match.winnerId = fencerB.id;
        match.scoreB = 'V';
        match.scoreA = '0';
      }

      firstRound.push(match);
    }

    // 4. 初始化后续轮次（空位）
    const allRounds = [firstRound];
    let currentSize = firstRound.length / 2;
    while (currentSize >= 1) {
      const roundMatches = Array.from({length: currentSize}, (_, i) => ({
        id: Math.random(), // 实际开发建议用固定 ID 规则
        fencerA: null,
        fencerB: null,
        scoreA: '',
        scoreB: '',
        winnerId: null
      }));
      allRounds.push(roundMatches);
      currentSize /= 2;
    }

    bracketData.value = allRounds;

    // 5. 自动将第一轮的轮空优胜者晋级
    firstRound.forEach((m, idx) => {
      if (m.winnerId) promoteWinner(m, 0, idx);
    });

    nextTick(drawLines);
  } catch (error) {
    console.error(error);
    ElMessage.error('初始化对阵表失败');
  } finally {
    loading.value = false;
  }
};

// 统一处理比分变更
const handleScoreChange = (rIdx: number, mIdx: number) => {
  const match = bracketData.value[rIdx][mIdx]

  // 1. 检查轮空 (Bye)
  if (!match.fencerA || !match.fencerB) {
    match.winnerId = match.fencerA?.id || match.fencerB?.id || null
  } else {
    // 2. 比较分数
    const sA = Number(match.scoreA) || 0
    const sB = Number(match.scoreB) || 0
    if (sA > sB) match.winnerId = match.fencerA.id
    else if (sB > sA) match.winnerId = match.fencerB.id
    else match.winnerId = null
  }

  // 3. 晋级到下一轮
  promoteWinner(match, rIdx, mIdx)

  // 4. 重绘线条（因为 winner 状态可能改变线条样式）
  drawLines()
}

// 晋级逻辑
const promoteWinner = (match: Match, rIdx: number, mIdx: number) => {
  if (rIdx >= bracketData.value.length - 1) return;
  const winner = match.winnerId === match.fencerA?.id ? match.fencerA : match.fencerB;
  const nextRoundMatch = bracketData.value[rIdx + 1][Math.floor(mIdx / 2)];

  if (mIdx % 2 === 0) nextRoundMatch.fencerA = winner;
  else nextRoundMatch.fencerB = winner;

  // 如果下一轮因为当前晋级也变成了“自动轮空”，则递归
  if (winner && (!nextRoundMatch.fencerA || !nextRoundMatch.fencerB)) {
    // 可以在这里处理连续轮空逻辑
  }
};

// --- 视图渲染辅助 ---

const setMatchRef = (el: HTMLElement | null, rIdx: number, mIdx: number) => {
  if (el) matchRefs.set(`${rIdx}-${mIdx}`, el)
}

const getSlotClass = (match: Match, side: 'A' | 'B') => {
  const fencer = side === 'A' ? match.fencerA : match.fencerB
  const isWinner = match.winnerId && fencer && match.winnerId === fencer.id
  return {
    'winner': isWinner,
    'bye-slot': !fencer
  }
}

// --- SVG 连线绘制 ---
const drawLines = () => {
  if (!viewportRef.value) return
  const newConnections: Connection[] = []
  const viewportRect = viewportRef.value.getBoundingClientRect()

  // 遍历每一轮（除最后一轮）
  for (let r = 0; r < bracketData.value.length - 1; r++) {
    const currentRound = bracketData.value[r]

    // 获取列之间的间隙中点作为折线转折点
    const currCol = matchRefs.get(`${r}-0`)?.parentElement?.parentElement
    const nextCol = matchRefs.get(`${r + 1}-0`)?.parentElement?.parentElement
    if (!currCol || !nextCol) continue

    // 遍历当前轮次比赛
    for (let m = 0; m < currentRound.length; m++) {
      const currEl = matchRefs.get(`${r}-${m}`)
      const nextEl = matchRefs.get(`${r + 1}-${Math.floor(m / 2)}`)
      if (!currEl || !nextEl) continue

      const startRect = currEl.getBoundingClientRect()
      const endRect = nextEl.getBoundingClientRect()

      // 坐标计算 (相对于 viewport)
      const startX = startRect.right - viewportRect.left
      const startY = startRect.top + startRect.height / 2 - viewportRect.top
      const endX = endRect.left - viewportRect.left
      const endY = endRect.top + endRect.height / 2 - viewportRect.top

      const midX = startX + (endX - startX) / 2

      // 绘制 "横-竖-横" 路径
      const d = `M ${startX} ${startY} H ${midX} V ${endY} H ${endX}`

      // 检查是否是轮空线 (虚线)
      const match = currentRound[m]
      const isBye = !match.fencerA || !match.fencerB

      newConnections.push({d, isBye})
    }
  }
  connections.value = newConnections
}

// --- 生命周期 ---
onMounted(() => {
  initRealDE();

  if (viewportRef.value) {
    resizeObserver = new ResizeObserver(() => requestAnimationFrame(drawLines))
    resizeObserver.observe(viewportRef.value)
  }
})

onUnmounted(() => {
  resizeObserver?.disconnect()
})
</script>

<style scoped lang="scss">
$border-color: #dcdfe6;
$winner-color: #67c23a;
$bg-color: #f8f9fa;

/* Mixins & Helpers */
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
  gap: 60px;
  padding: 40px 20px;
  position: relative;
  overflow-x: auto;
  min-height: 600px; /* 调整高度 */
}

.connection-layer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;

  .connection-line {
    fill: none;
    stroke: $border-color;
    stroke-width: 2;

    &.bye-connection {
      stroke-dasharray: 5, 5;
      stroke: #909399;
      opacity: 0.6;
    }
  }
}

.round-column {
  display: flex;
  flex-direction: column;
  min-width: 220px;
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
  position: relative;
  padding: 10px 0;
}

.match-box {
  background: white;
  border: 1px solid $border-color;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  transition: all 0.2s;

  &.has-winner {
    border-color: $winner-color;
    box-shadow: 0 2px 8px rgba(103, 194, 58, 0.15);
  }

  .fencer-slot {
    display: flex;
    align-items: center;
    height: 36px;
    padding: 0 0 0 10px; // 输入框自带左边框，所以右边距设为0

    .fencer-info {
      flex: 1;
      display: flex;
      justify-content: space-between; // 名字靠左，单位靠右
      align-items: center;
      overflow: hidden;
      margin-right: 8px;
    }

    .name {
      @include text-ellipsis;
      font-size: 12px;

      .ln {
        text-transform: uppercase; // 击剑惯例：姓氏大写
        font-weight: bold;
      }
    }

    .org {
      font-size: 10px;
      color: #909399;
      background: #f0f2f5;
      padding: 0 4px;
      border-radius: 2px;
      margin-left: 5px;
      flex-shrink: 0; // 确保国家代码不会被压缩
    }

    .score-input {
      width: 35px; // 略微加宽，防止两位数比分拥挤
      /* 其余样式保持不变 */
    }

    &.winner {
      background: #f0f9eb;
      color: $winner-color;
      font-weight: bold;
    }

    &.bye-slot {
      background: #f5f7fa;
      color: #c0c4cc;
      font-style: italic;
    }

    .seed {
      width: 24px;
      color: #999;
      font-size: 11px;
    }

    .name {
      flex: 1;
      @include text-ellipsis;
    }

    .bye-text {
      color: #c0c4cc;
    }

    .score-input {
      width: 32px;
      height: 100%;
      border: none;
      border-left: 1px solid #eee;
      text-align: center;
      font-weight: bold;
      background: transparent;
      outline: none;

      &:focus {
        background: #e6f7ff;
      }
    }
  }

  .divider {
    height: 1px;
    background: #eee;
  }
}

/* Responsive */
@media (max-width: 768px) {
  .bracket-viewport {
    gap: 30px;
    padding: 20px 10px;
  }
  .round-column {
    min-width: 160px;
  }
  .match-box .fencer-slot {
    height: 30px;
    font-size: 12px;
  }
}
</style>