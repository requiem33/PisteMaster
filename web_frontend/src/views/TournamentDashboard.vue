<template>
  <div class="page-container">
    <el-breadcrumb separator="/">
      <el-breadcrumb-item :to="{ path: '/' }">赛事中心</el-breadcrumb-item>
      <el-breadcrumb-item>2025年击剑公开赛</el-breadcrumb-item>
    </el-breadcrumb>

    <div class="header-actions mt-20">
      <h2>单项管理 (Events)</h2>
      <el-button type="success" icon="Plus">创建单项 (如：男重个人)</el-button>
    </div>

    <el-table :data="eventList" style="width: 100%" class="mt-20">
      <el-table-column prop="name" label="项目名称"/>
      <el-table-column prop="type" label="类别" width="120"/>
      <el-table-column prop="status" label="状态">
        <template #default="scope">
          <el-tag :type="scope.row.status === '进行中' ? 'warning' : 'info'">{{ scope.row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="scope">
          <el-button size="small" type="primary" @click="goToEvent(scope.row.id)">进入编排</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import {useRouter} from 'vue-router'

const router = useRouter()
const eventList = [
  {id: 101, name: '男子重剑个人 (ME)', type: '个人', status: '未开始'},
  {id: 102, name: '女子花剑个人 (WF)', type: '个人', status: '进行中'}
]
const goToEvent = (id: number) => router.push(`/event/${id}`)
</script>