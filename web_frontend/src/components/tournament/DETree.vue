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

    <div class="bracket-viewport" ref="viewport">
      <div v-for="(round, rIndex) in bracketData" :key="rIndex" class="round-column">
        <div class="round-header">Table of {{ Math.pow(2, bracketData.length - rIndex) }}</div>

        <div class="matches-container">
          <div v-for="(match, mIndex) in round" :key="mIndex" class="match-wrapper">
            <div class="match-box" :class="{ 'has-winner': match.winnerId }">
              <div class="fencer-slot" :class="{ 'winner': match.winnerId === match.fencerA?.id }">
                <span class="seed">{{ match.fencerA?.seed }}</span>
                <span class="name">{{ match.fencerA?.last_name || 'BYE' }}</span>
                <input
                    v-if="match.fencerA"
                    v-model="match.scoreA"
                    class="score-input"
                    @change="updateWinner(rIndex, mIndex)"
                />
              </div>

              <div class="divider"></div>

              <div class="fencer-slot" :class="{ 'winner': match.winnerId === match.fencerB?.id }">
                <span class="seed">{{ match.fencerB?.seed }}</span>
                <span class="name">{{ match.fencerB?.last_name || 'BYE' }}</span>
                <input
                    v-if="match.fencerB"
                    v-model="match.scoreB"
                    class="score-input"
                    @change="updateWinner(rIndex, mIndex)"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/* 路径：src/components/tournament/DETree.vue */
import {ref, onMounted} from 'vue'

const props = defineProps<{ eventId: string }>()
const viewBracket = ref('16')

// 模拟对阵数据结构
// 实际上这是根据上一步 PoolRanking 的结果自动填充的
const bracketData = ref<any[]>([])

const initMockDE = () => {
  // 模拟 Table of 8 -> 4 -> 2
  const t8 = [
    {
      id: 1,
      fencerA: {id: 'a1', last_name: 'KANO', seed: 1},
      fencerB: {id: 'a8', last_name: 'MINOBE', seed: 8},
      scoreA: 15,
      scoreB: 12,
      winnerId: 'a1'
    },
    {
      id: 2,
      fencerA: {id: 'a5', last_name: 'BOREL', seed: 5},
      fencerB: {id: 'a4', last_name: 'WANG', seed: 4},
      scoreA: 10,
      scoreB: 15,
      winnerId: 'a4'
    },
    {
      id: 3,
      fencerA: {id: 'a3', last_name: 'SIKLOSI', seed: 3},
      fencerB: {id: 'a6', last_name: 'LIMARDO', seed: 6},
      scoreA: 15,
      scoreB: 14,
      winnerId: 'a3'
    },
    {
      id: 4,
      fencerA: {id: 'a7', last_name: 'PARK', seed: 7},
      fencerB: {id: 'a2', last_name: 'CHUMAK', seed: 2},
      scoreA: 13,
      scoreB: 15,
      winnerId: 'a2'
    },
  ]
  const t4 = [
    {id: 5, fencerA: t8[0].fencerA, fencerB: t8[1].fencerB, scoreA: '', scoreB: '', winnerId: null},
    {id: 6, fencerA: t8[2].fencerA, fencerB: t8[3].fencerB, scoreA: '', scoreB: '', winnerId: null},
  ]
  const t2 = [
    {id: 7, fencerA: null, fencerB: null, scoreA: '', scoreB: '', winnerId: null}
  ]

  bracketData.value = [t8, t4, t2]
}

const updateWinner = (rIndex: number, mIndex: number) => {
  const match = bracketData.value[rIndex][mIndex]
  const sA = parseInt(match.scoreA) || 0
  const sB = parseInt(match.scoreB) || 0

  if (sA > sB) match.winnerId = match.fencerA.id
  else if (sB > sA) match.winnerId = match.fencerB.id

  // 逻辑：将赢家自动推送到下一轮
  if (rIndex < bracketData.value.length - 1) {
    const nextMatchIndex = Math.floor(mIndex / 2)
    const nextMatch = bracketData.value[rIndex + 1][nextMatchIndex]
    const winnerObj = sA > sB ? match.fencerA : match.fencerB

    if (mIndex % 2 === 0) nextMatch.fencerA = winnerObj
    else nextMatch.fencerB = winnerObj
  }
}

onMounted(initMockDE)
</script>

<style scoped lang="scss">
.de-tree-container {
  background: #f8f9fa;
  padding: 20px;
  min-height: 600px;
}

.tree-controls {
  margin-bottom: 30px;
  display: flex;
  justify-content: space-between;
}

.bracket-viewport {
  display: flex;
  overflow-x: auto;
  gap: 60px;
  padding: 40px 20px;
}

.round-column {
  display: flex;
  flex-direction: column;
  min-width: 220px;

  .round-header {
    text-align: center;
    font-weight: bold;
    color: #909399;
    margin-bottom: 20px;
    text-transform: uppercase;
    font-size: 12px;
  }
}

.matches-container {
  display: flex;
  flex-direction: column;
  justify-content: space-around; /* 核心：自动拉开对阵间距 */
  flex-grow: 1;
}

.match-wrapper {
  position: relative;
  padding: 15px 0;
}

.match-box {
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  overflow: hidden;

  .fencer-slot {
    display: flex;
    align-items: center;
    height: 35px;
    padding: 0 10px;
    font-size: 13px;
    background: #fff;

    &.winner {
      background: #f0f9eb;
      color: #67c23a;
      font-weight: bold;
    }

    .seed {
      width: 25px;
      color: #999;
      font-size: 11px;
    }

    .name {
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .score-input {
      width: 30px;
      border: none;
      border-left: 1px solid #eee;
      text-align: center;
      font-weight: bold;
      height: 100%;
      outline: none;
      background: transparent;
    }
  }

  .divider {
    height: 1px;
    background: #eee;
  }
}

/* 绘制树形连接线（示例仅针对前两轮） */
.round-column:not(:last-child) .match-wrapper::after {
  content: "";
  position: absolute;
  right: -60px;
  top: 50%;
  width: 60px;
  height: 100%;
  border: 2px solid #dcdfe6;
  border-left: none;
  z-index: 0;
}

/* 奇数和偶数匹配不同的连线高度，此处代码略，实际通常使用更复杂的动态计算 */
</style>