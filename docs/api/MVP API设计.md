# PisteMaster MVP API设计

## MVP目标

实现击剑赛事管理的**最小可行产品**，支持个人赛完整流程：
创建赛事 → 创建项目 → 导入/同步运动员 → 小组赛排阵与成绩记录 → 淘汰赛排阵与成绩记录 → 最终成绩。

> **注**：前端目前使用类似“乐观UI/本地计算”模式，大量逻辑（如排阵、算分）在前端本地完成，后端需提供支持大块数据（如JSON）直接存储与同步的接口，以匹配前端 `DataManager.ts` 的实际需求。

---

## 核心API设计

### 1. 赛事管理 API (Tournament)

#### 1.1 创建赛事
```http
POST /api/tournaments/
```
**请求体:**
```json
{
  "tournament_name": "2024全国击剑锦标赛",
  "organizer": "中国击剑协会",
  "location": "北京国家体育中心",
  "start_date": "2024-06-01",
  "end_date": "2024-06-05"
}
```

#### 1.2 获取赛事列表
```http
GET /api/tournaments/
```

#### 1.3 获取赛事详情
```http
GET /api/tournaments/{tournament_id}/
```

#### 1.4 更新赛事
```http
PUT /api/tournaments/{tournament_id}/
```
**请求体:** 同创建赛事。

#### 1.5 删除赛事
```http
DELETE /api/tournaments/{tournament_id}/
```

---

### 2. 项目管理 API (Event)

#### 2.1 创建比赛项目
```http
POST /api/events/
```
**请求体:**
```json
{
  "tournament_id": "uuid",
  "event_name": "男子个人花剑",
  "event_type_id": "MEN_INDIVIDUAL_FOIL",
  "rule_id": "uuid",
  "is_team_event": false,
  "status": "正在报名"
}
```

#### 2.2 获取项目列表 (按赛事)
```http
GET /api/tournaments/{tournament_id}/events/
```

#### 2.3 获取项目详情
```http
GET /api/events/{event_id}/
```

#### 2.4 更新项目 (含当前进度)
```http
PUT /api/events/{event_id}/
```
**请求体:**
```json
{
  "event_name": "男子个人花剑",
  "status": "正在进行",
  "current_step": 2
}
```

#### 2.5 删除项目
```http
DELETE /api/events/{event_id}/
```

---

### 3. 运动员与报名管理 API (Fencer & Participants)

#### 3.1 批量保存/更新运动员信息 (全局库)
```http
POST /api/fencers/bulk-save/
```
前端会在导入运动员时调用，以 fencing_id 或其他标识更新或创建全局运动员。
**请求体:**
```json
[
  {
    "fencing_id": "CFA12345",
    "first_name": "三",
    "last_name": "张",
    "country_code": "CHN",
    "current_ranking": 5
  }
]
```

#### 3.2 覆盖式同步项目参赛名单
```http
PUT /api/events/{event_id}/participants/sync/
```
根据前端传来的所有 `fencer_id` 列表，覆盖该项目原有的所有关联名单。
**请求体:**
```json
{
  "fencer_ids": [
    "550e8400-...",
    "550e8401-..."
  ]
}
```

#### 3.3 获取项目参赛选手完整信息
```http
GET /api/events/{event_id}/participants/
```
返回该项目下所有参赛选手的详细信息（联表查询 `fencer` 表）。

---

### 4. 赛事状态与排名管理 API (Live Ranking)

前端在 Event 下维护了一个 `live_ranking` 的 JSON 结构，用于存储选手在各阶段的晋级与排名状态。

#### 4.1 初始化/全量更新实时排名
```http
PUT /api/events/{event_id}/live-ranking/
```
**请求体:**
```json
{
  "live_ranking": [
    {
      "id": "fencer_uuid_1",
      "ranks": { "0": 1, "1": 1 },
      "elimination_status": { "0": false, "1": false }
    }
  ]
}
```

#### 4.2 获取实时排名
可以随项目详情 `GET /api/events/{event_id}/` 一并返回，或单独 `GET /api/events/{event_id}/live-ranking/`。

---

### 5. 小组赛管理 API (Pools)

前端自己完成分组算法，直接将分组结果（带阶段 ID）保存到后端。

#### 5.1 批量保存某阶段分组
```http
POST /api/events/{event_id}/stages/{stage_id}/pools/
```
**请求体:**
```json
[
  {
    "pool_number": 1,
    "fencer_ids": ["uuid_1", "uuid_2", "uuid_3"]
  },
  {
    "pool_number": 2,
    "fencer_ids": ["uuid_4", "uuid_5", "uuid_6"]
  }
]
```

#### 5.2 获取某阶段所有分组
```http
GET /api/events/{event_id}/stages/{stage_id}/pools/
```

#### 5.3 更新单组比赛结果矩阵与统计 (Results & Stats)
```http
PATCH /api/pools/{pool_id}/results/
```
**请求体:**
```json
{
  "results": [[null, "V5", "D3"], ["D2", null, "V5"], ["V5", "D1", null]],
  "stats": [
    { "V": 2, "TS": 10, "TR": 5, "Ind": 5 },
    { "V": 1, "TS": 7, "TR": 8, "Ind": -1 },
    { "V": 0, "TS": 4, "TR": 10, "Ind": -6 }
  ],
  "is_locked": true
}
```
*注：由于前端以矩阵（二维数组）形式暂存循环赛比分，MVP 阶段后端可直接以 JSONField 存储 `results` 和 `stats`，便于快速对齐。未来可按需拆分为独立的 Bouts 记录。*

---

### 6. 淘汰赛管理 API (DE Tree)

前端在计算淘汰赛对阵后，生成完整的对阵树形结构（嵌套数组或对象）。

#### 6.1 保存某阶段淘汰赛对阵图
```http
PUT /api/events/{event_id}/stages/{stage_id}/detree/
```
**请求体:**
```json
{
  "tree_data": [
    [ 
      {"match_id": 1, "fencerA": {...}, "fencerB": {...}, "winnerId": "uuid"} 
    ],
    [
      {"match_id": 2, "fencerA": {...}, "fencerB": {...}}
    ]
  ]
}
```

#### 6.2 获取某阶段淘汰赛对阵图
```http
GET /api/events/{event_id}/stages/{stage_id}/detree/
```
*注：对应 `DataManager.getDETree`。与 Pool 类似，使用 JSONField 直接存取以适配当前前端逻辑。*

---

## 架构适配总结 (CQRS 与离线优先)

前端 `DataManager.ts` 中的逻辑主要是：
1. 本地生成数据（如算法算分、排阵）。
2. 写本地 IndexedDB（保证离线高可用与极速响应）。
3. **需要异步向后端发送整块构建好的数据**，而不是频繁调动细粒度的 `计算` API。

因此，MVP 的后端接口设计相较于传统的“后端负责计算”模式，更倾向于**“文档存储”**模式（使用 JSONField 或关联表的批量覆盖），即：前端算完，后端存盘；前端拉取，恢复状态。

状态码与错误处理同上文规范。