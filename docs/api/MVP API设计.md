# PisteMaster MVP API设计

## MVP目标
实现击剑赛事管理的**最小可行产品**，支持个人赛完整流程：
1. 创建赛事 → 2. 创建项目 → 3. 选择规则 → 4. 添加运动员 → 5. 创建小组 → 6. 生成比赛 → 7. 登记结果 → 8. 计算排名

## 核心API设计

### 1. 赛事管理 API

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
  "end_date": "2024-06-05",
  "status_id": "PLANNING"
}
```

**响应:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "tournament_name": "2024全国击剑锦标赛",
  "status": "PLANNING",
  "created_at": "2024-01-15T10:00:00Z"
}
```

#### 1.2 获取赛事列表
```http
GET /api/tournaments/
```

**查询参数:**
- `status` (可选): 按状态过滤
- `start_date__gte` (可选): 开始日期之后
- `end_date__lte` (可选): 结束日期之前

**响应:**
```json
{
  "count": 3,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "tournament_name": "2024全国击剑锦标赛",
      "status": "PLANNING",
      "start_date": "2024-06-01",
      "end_date": "2024-06-05",
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

---

### 2. 项目管理 API

#### 2.1 创建比赛项目（个人赛）
```http
POST /api/tournaments/{tournament_id}/events/
```

**请求体:**
```json
{
  "event_name": "男子个人花剑",
  "event_type_id": "MEN_INDIVIDUAL_FOIL",
  "rule_id": "550e8400-e29b-41d4-a716-446655440001",
  "start_time": "2024-06-01T09:00:00Z",
  "is_team_event": false
}
```

**响应:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "event_name": "男子个人花剑",
  "event_type": "MEN_INDIVIDUAL_FOIL",
  "status": "SCHEDULED",
  "is_team_event": false,
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### 2.2 获取项目详情
```http
GET /api/events/{event_id}/
```

**响应:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "tournament": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "2024全国击剑锦标赛"
  },
  "event_name": "男子个人花剑",
  "event_type": "MEN_INDIVIDUAL_FOIL",
  "rule": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "标准赛制",
    "pool_size": 7,
    "match_score_pool": 5,
    "match_score_elimination": 15,
    "total_qualified_count": 24
  },
  "status": "SCHEDULED",
  "participant_count": 0,
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### 3. 规则管理 API

#### 3.1 获取可用规则列表
```http
GET /api/rules/
```

**响应:**
```json
{
  "count": 4,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "rule_name": "标准赛制",
      "pool_size": 7,
      "match_score_pool": 5,
      "match_score_elimination": 15,
      "total_qualified_count": 24,
      "description": "标准FIE比赛规则：小组赛7人一组，5分制，淘汰赛15分制"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440003",
      "rule_name": "快速赛制",
      "pool_size": 6,
      "match_score_pool": 10,
      "match_score_elimination": 15,
      "total_qualified_count": 16,
      "description": "快速比赛规则：小组赛6人一组，10分制"
    }
  ]
}
```

---

### 4. 运动员管理 API

#### 4.1 添加运动员到项目
```http
POST /api/events/{event_id}/participants/
```

**请求体（单个添加）:**
```json
{
  "fencer_id": "550e8400-e29b-41d4-a716-446655440010"
}
```

**请求体（批量添加）:**
```json
{
  "fencer_ids": [
    "550e8400-e29b-41d4-a716-446655440010",
    "550e8400-e29b-41d4-a716-446655440011",
    "550e8400-e29b-41d4-a716-446655440012"
  ]
}
```

**响应:**
```json
{
  "success": true,
  "added_count": 3,
  "total_participants": 3,
  "participants": [
    {
      "fencer_id": "550e8400-e29b-41d4-a716-446655440010",
      "name": "张三",
      "country_code": "CHN",
      "seed_rank": 1
    }
  ]
}
```

#### 4.2 获取项目运动员列表
```http
GET /api/events/{event_id}/participants/
```

**查询参数:**
- `with_seeds` (可选, boolean): 是否包含种子排名

**响应:**
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440002",
  "participant_count": 42,
  "participants": [
    {
      "fencer": {
        "id": "550e8400-e29b-41d4-a716-446655440010",
        "first_name": "三",
        "last_name": "张",
        "display_name": "张三",
        "country_code": "CHN",
        "current_ranking": 5
      },
      "seed_rank": 1,
      "seed_value": 100.0
    }
  ]
}
```

---

### 5. 小组管理 API

#### 5.1 自动分组
```http
POST /api/events/{event_id}/pools/generate/
```

**请求体:**
```json
{
  "method": "SEEDED",  // 或 "RANDOM", "MANUAL"
  "pool_size": 7,
  "ignore_seeds": false
}
```

**响应:**
```json
{
  "success": true,
  "pool_count": 6,
  "participants_per_pool": [7, 7, 7, 7, 7, 7],
  "pools": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440101",
      "pool_number": 1,
      "pool_letter": "A",
      "fencer_count": 7,
      "fencer_ids": ["550e8400-e29b-41d4-a716-446655440010", "..."]
    }
  ]
}
```

#### 5.2 获取项目所有小组
```http
GET /api/events/{event_id}/pools/
```

**响应:**
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440002",
  "pool_count": 6,
  "pools": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440101",
      "pool_number": 1,
      "pool_letter": "A",
      "fencer_count": 7,
      "status": "SCHEDULED",
      "start_time": "2024-06-01T09:00:00Z"
    }
  ]
}
```

---

### 6. 小组赛比赛管理 API

#### 6.1 生成小组赛对阵
```http
POST /api/pools/{pool_id}/bouts/generate/
```

**请求体:**
```json
{
  "format": "ROUND_ROBIN"  // 循环赛制
}
```

**响应:**
```json
{
  "success": true,
  "generated_count": 21,  // 7人小组的比赛数：C(7,2)=21
  "bouts": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440201",
      "fencer_a_id": "550e8400-e29b-41d4-a716-446655440010",
      "fencer_b_id": "550e8400-e29b-41d4-a716-446655440011",
      "scheduled_time": "2024-06-01T09:00:00Z",
      "status": "SCHEDULED"
    }
  ]
}
```

#### 6.2 获取小组比赛列表
```http
GET /api/pools/{pool_id}/bouts/
```

**查询参数:**
- `status` (可选): 按状态过滤
- `date` (可选): 按日期过滤

**响应:**
```json
{
  "pool_id": "550e8400-e29b-41d4-a716-446655440101",
  "bout_count": 21,
  "completed_count": 0,
  "bouts": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440201",
      "fencer_a": {
        "id": "550e8400-e29b-41d4-a716-446655440010",
        "name": "张三",
        "country_code": "CHN"
      },
      "fencer_b": {
        "id": "550e8400-e29b-41d4-a716-446655440011",
        "name": "李四",
        "country_code": "CHN"
      },
      "score_a": 0,
      "score_b": 0,
      "winner_id": null,
      "status": "SCHEDULED",
      "scheduled_time": "2024-06-01T09:00:00Z",
      "actual_start_time": null,
      "actual_end_time": null
    }
  ]
}
```

---

### 7. 比赛结果登记 API

#### 7.1 更新比赛结果（单个）
```http
PATCH /api/bouts/{bout_id}/
```

**请求体:**
```json
{
  "fencer_a_score": 5,
  "fencer_b_score": 3,
  "winner_id": "550e8400-e29b-41d4-a716-446655440010",
  "status_id": "COMPLETED",
  "actual_start_time": "2024-06-01T09:05:00Z",
  "actual_end_time": "2024-06-01T09:10:00Z"
}
```

**响应:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440201",
  "fencer_a_score": 5,
  "fencer_b_score": 3,
  "winner_id": "550e8400-e29b-41d4-a716-446655440010",
  "status": "COMPLETED",
  "duration_seconds": 300,
  "updated_at": "2024-01-15T11:00:00Z"
}
```

#### 7.2 批量登记比赛结果
```http
POST /api/pools/{pool_id}/bouts/batch-update/
```

**请求体:**
```json
{
  "results": [
    {
      "bout_id": "550e8400-e29b-41d4-a716-446655440201",
      "fencer_a_score": 5,
      "fencer_b_score": 3,
      "winner_id": "550e8400-e29b-41d4-a716-446655440010"
    },
    {
      "bout_id": "550e8400-e29b-41d4-a716-446655440202",
      "fencer_a_score": 5,
      "fencer_b_score": 2,
      "winner_id": "550e8400-e29b-41d4-a716-446655440012"
    }
  ]
}
```

**响应:**
```json
{
  "success": true,
  "updated_count": 2,
  "failed_count": 0,
  "results": [
    {
      "bout_id": "550e8400-e29b-41d4-a716-446655440201",
      "status": "SUCCESS"
    }
  ]
}
```

---

### 8. 小组排名计算 API

#### 8.1 计算小组排名
```http
POST /api/pools/{pool_id}/calculate-ranking/
```

**响应:**
```json
{
  "success": true,
  "pool_id": "550e8400-e29b-41d4-a716-446655440101",
  "calculated_at": "2024-01-15T11:30:00Z",
  "rankings": [
    {
      "fencer_id": "550e8400-e29b-41d4-a716-446655440010",
      "final_pool_rank": 1,
      "victories": 6,
      "indicator": 20,
      "touches_scored": 30,
      "touches_received": 10,
      "is_qualified": true,
      "qualification_rank": 1
    },
    {
      "fencer_id": "550e8400-e29b-41d4-a716-446655440011",
      "final_pool_rank": 2,
      "victories": 5,
      "indicator": 15,
      "touches_scored": 28,
      "touches_received": 13,
      "is_qualified": true,
      "qualification_rank": 2
    }
  ]
}
```

#### 8.2 获取小组排名
```http
GET /api/pools/{pool_id}/rankings/
```

**查询参数:**
- `qualified_only` (可选, boolean): 仅显示晋级选手

**响应:**
```json
{
  "pool_id": "550e8400-e29b-41d4-a716-446655440101",
  "last_calculated": "2024-01-15T11:30:00Z",
  "is_completed": true,
  "rankings": [
    {
      "rank": 1,
      "fencer": {
        "id": "550e8400-e29b-41d4-a716-446655440010",
        "name": "张三",
        "country_code": "CHN"
      },
      "victories": 6,
      "indicator": 20,
      "ts": 30,
      "tr": 10,
      "matches_played": 6,
      "is_qualified": true,
      "qualification_rank": 1
    }
  ]
}
```

#### 8.3 获取项目总体晋级名单
```http
GET /api/events/{event_id}/qualifiers/
```

**响应:**
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440002",
  "total_qualified": 24,
  "qualification_status": "COMPLETED",
  "qualifiers": [
    {
      "overall_rank": 1,
      "fencer": {
        "id": "550e8400-e29b-41d4-a716-446655440010",
        "name": "张三",
        "country_code": "CHN"
      },
      "pool_rank": 1,
      "pool_letter": "A",
      "victories": 6,
      "indicator": 20
    }
  ]
}
```

---

## 扩展API（MVP增强）

### 9. 赛事状态管理

#### 9.1 更新赛事状态
```http
PATCH /api/tournaments/{tournament_id}/status/
```
```json
{
  "status_id": "ONGOING"
}
```

#### 9.2 更新项目状态
```http
PATCH /api/events/{event_id}/status/
```
```json
{
  "status_id": "POOL_ROUND"
}
```

### 10. 数据导出API

#### 10.1 导出项目数据
```http
GET /api/events/{event_id}/export/
```
**查询参数:**
- `format`: `json`, `csv`, `pdf`
- `include`: `participants`, `pools`, `bouts`, `rankings`

---

## API状态码

| 状态码 | 含义 | 场景 |
|--------|------|------|
| 200 | 成功 | 获取数据成功 |
| 201 | 创建成功 | 资源创建成功 |
| 400 | 请求错误 | 参数验证失败 |
| 404 | 未找到 | 资源不存在 |
| 409 | 冲突 | 重复创建、状态冲突 |
| 422 | 业务逻辑错误 | 分组失败、计算失败 |

---

## 工作流程示例

### 完整流程API调用顺序

```bash
# 1. 创建赛事
POST /api/tournaments/

# 2. 创建项目
POST /api/tournaments/{tournament_id}/events/

# 3. 添加运动员到项目
POST /api/events/{event_id}/participants/

# 4. 自动分组
POST /api/events/{event_id}/pools/generate/

# 5. 生成小组赛对阵
POST /api/pools/{pool_id}/bouts/generate/

# 6. 登记比赛结果
PATCH /api/bouts/{bout_id}/

# 7. 计算小组排名
POST /api/pools/{pool_id}/calculate-ranking/

# 8. 获取晋级名单
GET /api/events/{event_id}/qualifiers/
```

---

## 权限设计（MVP简化版）

### 角色
- **管理员**: 全部操作权限
- **裁判**: 登记比赛结果、查看比赛数据
- **观众**: 只读权限

### 权限控制
```python
# 简单实现示例
PERMISSIONS = {
    'admin': ['*'],
    'referee': ['GET', 'PATCH'],  # 可查看和更新比赛
    'viewer': ['GET']  # 只读
}
```

---

## 数据验证规则

### 业务规则示例

1. **分组规则**:
   - 小组人数必须符合规则设置（3-7人）
   - 种子选手均匀分布

2. **比赛结果验证**:
   - 比分必须小于等于目标分数（小组赛5分，淘汰赛15分）
   - 胜者必须是对阵双方之一
   - 比赛不能重复登记

3. **排名计算规则**:
   - 先看胜场数(V)
   - 再看Indicator(TS-TR)
   - 最后看TS（总得分）

---

## API速率限制（MVP）

| API类型 | 限制 |
|---------|------|
| 创建操作 | 10次/分钟 |
| 更新操作 | 30次/分钟 |
| 查询操作 | 60次/分钟 |

---

## 错误响应格式

```json
{
  "error": {
    "code": "INVALID_SCORE",
    "message": "比分不能超过目标分数5分",
    "details": {
      "field": "fencer_a_score",
      "value": 6,
      "constraint": "max_value=5"
    }
  },
  "timestamp": "2024-01-15T12:00:00Z"
}
```

---

这个MVP API设计覆盖了个人赛的核心流程，可以在后续版本中扩展团体赛、淘汰赛、裁判管理等功能。建议先实现基础版本，然后根据用户反馈逐步完善。