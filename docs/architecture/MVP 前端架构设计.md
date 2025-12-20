# PisteMaster 前端架构设计文档 - MVP 增强版

## 🎯 项目概述

PisteMaster 是一款专为击剑赛事设计的编排与计分软件。针对比赛现场**网络波动大、实时性要求高、需物理打印、硬件交互**
等核心痛点，本架构采用了“离线优先 (Offline-First)”与“仓库模式 (Repository Pattern)”的设计理念。

---

## 📦 技术栈选型

### 1. 核心框架与构建

* **Vue 3.4+ (Composition API)**: 响应式业务逻辑。
* **TypeScript 5.0+**: 严格类型约束，减少计分逻辑错误。
* **Vite 5.0+**: 极速开发与构建。
* **Vite-plugin-pwa**: 实现离线访问与应用级安装体验。

### 2. 状态与数据流

* **Pinia 2.1+**: 全局状态管理（用户信息、当前赛事上下文）。
* **Repository Pattern**: 抽象数据层，统一处理 `IndexedDB` 与 `Django API` 的同步策略。
* **LocalForage (IndexedDB)**: 本地持久化存储，支持大规模运动员数据缓存。

### 3. 实时性与交互

* **WebSocket (Socket.io-client)**: 与 Django Channels 配合，实现计分实时推送到大屏幕。
* **Web Serial API**: 探索性支持，用于直接读取物理计分器（Favero/StM）数据。

### 4. UI 与 展现

* **Element Plus**: 编排后台管理。
* **Custom CSS/Tailwind**: 针对裁判端（平板）的大按钮、高对比度触控优化。
* **Vue3-print-nb / jsPDF**: 赛事成绩单、小组表、对阵表的打印与生成。

---

## 🏗️ 改进后的项目架构

```
web-frontend/
├── src/
│   ├── api/                  # 基础通信层
│   │   ├── axios.ts          # Django REST 拦截器
│   │   └── websocket.ts      # Django Channels 连接逻辑
│   ├── repositories/         # 👈 数据仓库层（核心改进）
│   │   ├── MatchRepository.ts# 处理：UI <-> LocalDB <-> Remote API
│   │   ├── FencerRepository.ts
│   │   └── SyncManager.ts    # 冲突检测与增量同步算法
│   ├── components/
│   │   ├── scoring/          # 计分端专用（高可靠性、大字体）
│   │   ├── tournament/       # 赛事编排组件
│   │   └── shared/           # 通用表格、打印模板
│   ├── hooks/                # 业务逻辑封装 (Composables)
│   │   ├── useMatchTimer.ts  # 击剑 3 分钟倒计时逻辑
│   │   ├── useHardware.ts   # Web Serial 串口通信
│   │   └── useOffline.ts     # 网络状态监控
│   ├── stores/               # Pinia 状态管理
│   │   ├── auth.store.ts     # 权限与角色 (编排长/裁判/观众)
│   │   └── app.store.ts      # 全局配置 (语言、当前赛季)
│   ├── styles/
│   │   ├── theme/            # 主题色
│   │   └── print.scss        # 👈 专门的打印媒体查询样式
│   ├── utils/
│   │   ├── fencing/          # 击剑核心算法 (胜率计算、名次排序)
│   │   └── pdf-gen.ts        # PDF 生成工具类
│   ├── views/                # 页面级视图
│   └── types/                # TS 类型定义 (models.d.ts, api.d.ts)
├── public/                   # 静态资源及 PWA 图标
├── vite.config.ts            # PWA 与 代理配置
└── package.json
```

---

## 🛠️ 核心功能设计优化

### 1. 离线优先同步策略 (Offline-First)

* **写入路径**: 裁判点击加分 -> 直接写入 `MatchRepository` -> 立即更新 `IndexedDB` 并反馈 UI -> 触发后台同步任务尝试推送给
  Django。
* **冲突解决**: 采用 `updated_at` 时间戳对比，若本地与服务器版本不一致，弹出冲突确认框或以服务器为准。

### 2. 实时计分广播 (Real-time)

* 通过 `src/api/websocket.ts` 监听 Django Channels。
* **场景**: 当裁判端更新比分，Django 广播 `match_update` 消息，大屏幕端（Spectator View）自动更新 UI，无需刷新。

### 3. 击剑专业报表打印 (Print & PDF)

* **小组循环表**: 自动生成横纵交叉表格。
* **淘汰赛对阵表 (Brackets)**: 使用 SVG 或 Canvas 绘制，并支持一键导出为 PDF 存档。
* **技术方案**: 专用打印页面路由 + CSS `@media print` 隐藏导航栏与多余按钮。

### 4. 权限与路由安全

* **RBAC 模型**:
* `Admin`: 完整赛事编排权限。
* `Referee`: 仅限分配给自己的比赛计分权限。
* `Public`: 只读访问实时比分与排名。


* **路由守卫**: 结合 `auth.store.ts` 拦截非法访问，确保计分端不被误操作。

---

## 📈 MVP 迭代里程碑

| 阶段           | 重点      | 交付物                             |
|--------------|---------|---------------------------------|
| **L1: 核心编排** | 基础 CRUD | 运动员导入、小组自动分配、Django API 对接。     |
| **L2: 离线计分** | 数据可靠性   | IndexedDB 集成、PWA 配置、离线状态下的计分操作。 |
| **L3: 实时互联** | 现场体验    | WebSocket 实时比分、大屏幕显示、自动同步机制。    |
| **L4: 闭环导出** | 文档合规    | PDF 成绩单导出、小组表打印、最终名次计算。         |

---