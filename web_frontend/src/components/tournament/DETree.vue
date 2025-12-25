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
                  <span class="name">{{ match.fencerA.last_name }}</span>
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
                  <span class="name">{{ match.fencerB.last_name }}</span>
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

// --- 类型定义 ---
interface Fencer {
  id: string
  last_name: string
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

const viewportRef = ref<HTMLElement>()
const matchRefs = new Map<string, HTMLElement>()
let resizeObserver: ResizeObserver | null = null

// --- 核心逻辑 ---

// 初始化数据
const initMockDE = () => {
  const fencers = {
    a1: {id: 'a1', last_name: 'KANO', seed: 1},
    a2: {id: 'a2', last_name: 'CHUMAK', seed: 2},
    a3: {id: 'a3', last_name: 'SIKLOSI', seed: 3},
    a4: {id: 'a4', last_name: 'WANG', seed: 4},
    a5: {id: 'a5', last_name: 'BOREL', seed: 5},
    a6: {id: 'a6', last_name: 'LIMARDO', seed: 6},
    a7: {id: 'a7', last_name: 'PARK', seed: 7},
    a8: {id: 'a8', last_name: 'MINOBE', seed: 8}
  }

  const t8: Match[] = [
    {id: 1, fencerA: fencers.a1, fencerB: fencers.a8, scoreA: 15, scoreB: 12, winnerId: 'a1'},
    {id: 2, fencerA: fencers.a5, fencerB: fencers.a4, scoreA: 10, scoreB: 15, winnerId: 'a4'},
    {id: 3, fencerA: fencers.a3, fencerB: fencers.a6, scoreA: 15, scoreB: 14, winnerId: 'a3'},
    {id: 4, fencerA: fencers.a7, fencerB: fencers.a2, scoreA: 13, scoreB: 15, winnerId: 'a2'},
  ]

  // 仅占位，数据由上一轮填充
  const createEmptyMatch = (id: number): Match => ({
    id, fencerA: null, fencerB: null, scoreA: '', scoreB: '', winnerId: null
  })

  // 预填 T4 (基于 T8 结果)
  const t4 = [
    {...createEmptyMatch(5), fencerA: t8[0].fencerA, fencerB: t8[1].fencerB}, // 简化模拟逻辑
    {...createEmptyMatch(6), fencerA: t8[2].fencerA, fencerB: t8[3].fencerB}
  ]
  const t2 = [createEmptyMatch(7)]

  bracketData.value = [t8, t4, t2]
  nextTick(drawLines)
}

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
  if (rIdx >= bracketData.value.length - 1) return // 决赛无下一轮

  const winner = match.winnerId === match.fencerA?.id ? match.fencerA : match.fencerB
  const nextRoundMatch = bracketData.value[rIdx + 1][Math.floor(mIdx / 2)]

  // 根据当前是偶数还是奇数位置，决定放入下一轮的 A 位还是 B 位
  if (mIdx % 2 === 0) nextRoundMatch.fencerA = winner
  else nextRoundMatch.fencerB = winner

  // 如果下一轮因此变成轮空（例如对手还没产生），递归检查
  if (winner && (!nextRoundMatch.fencerA || !nextRoundMatch.fencerB)) {
    // 这里可以选择是否自动处理下一轮的轮空胜出，视规则而定
    // 简单起见，这里只更新数据，UI会自动响应
  }
}

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
  initMockDE()

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
    padding: 0 10px;
    font-size: 13px;
    background: #fff;

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