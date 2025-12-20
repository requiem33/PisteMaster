<template>
  <div class="page-container">
    <el-page-header icon="" title="PisteMaster">
      <template #content><span class="text-large font-600"> 赛事中心 </span></template>
      <template #extra>
        <el-button type="primary" icon="Plus" @click="showCreate = true">创建新赛事</el-button>
      </template>
    </el-page-header>

    <el-row :gutter="20" class="mt-20">
      <el-col :span="8" v-for="i in 3" :key="i">
        <el-card shadow="hover" class="tournament-card" @click="goToTournament(i)">
          <h3>2025年击剑公开赛 #{{ i }}</h3>
          <p>
            <el-icon>
              <Calendar/>
            </el-icon>
            2025-12-20
          </p>
          <p>
            <el-icon>
              <Location/>
            </el-icon>
            体育馆中心
          </p>
          <div class="card-footer">
            <el-tag>6个单项</el-tag>
            <el-button type="primary" link>管理赛事
              <el-icon>
                <ArrowRight/>
              </el-icon>
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="showCreate" title="新建赛事" width="500px">
      <el-form label-position="top">
        <el-form-item label="赛事名称">
          <el-input placeholder="请输入赛事名称"/>
        </el-form-item>
        <el-form-item label="地点">
          <el-input placeholder="请输入比赛地点"/>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button type="primary" @click="showCreate = false">确认创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import {ref} from 'vue'
import {useRouter} from 'vue-router'

const router = useRouter()
const showCreate = ref(false)
const goToTournament = (id: number) => router.push(`/tournament/${id}`)
</script>