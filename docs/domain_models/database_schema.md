# PisteMaster数据库架构文档

**版本:** v0.1  
**更新日期:** 2025年12月10日  
**设计重点:**

1. 全面采用 UUID 支持分布式系统
2. 个人赛与团体赛对称结构，支持复杂晋级树
3. 增强数据规范化与查询性能
4. 支持裁判、场地、时间管理等实际赛事需求

---

## 📋 目录

1. [核心赛事结构](#1-核心赛事结构)
2. [枚举与配置表](#2-枚举与配置表)
3. [运动员及队伍管理](#3-运动员及队伍管理)
4. [小组赛模型](#4-小组赛模型)
5. [个人淘汰赛模型](#5-个人淘汰赛模型)
6. [团体淘汰赛模型](#6-团体淘汰赛模型)
7. [裁判与场地管理](#7-裁判与场地管理)
8. [性能优化设计](#8-性能优化设计)
9. [扩展功能表](#9-扩展功能表)

---

## 1. 核心赛事结构

### 1.1. Tournament（赛事主表）

| 属性              | 类型           | 约束                         | 描述        |
|:----------------|:-------------|:---------------------------|:----------|
| **id**          | UUID         | PK                         | 主键，全局唯一标识 |
| tournament_name | VARCHAR(200) | NOT NULL                   | 赛事名称      |
| organizer       | VARCHAR(200) |                            | 主办方       |
| location        | VARCHAR(200) |                            | 赛事举办地     |
| start_date      | DATE         | NOT NULL                   | 开始日期      |
| end_date        | DATE         | NOT NULL                   | 结束日期      |
| **status_id**   | UUID         | FK → Tournament_Status(id) | 赛事状态      |
| created_at      | TIMESTAMP    | DEFAULT NOW()              | 创建时间      |
| updated_at      | TIMESTAMP    | DEFAULT NOW()              | 更新时间      |

**索引:**

- `idx_tournament_dates` (start_date, end_date)
- `idx_tournament_status` (status_id)

---

### 1.2. Event（比赛项目）

| 属性                | 类型           | 约束                    | 描述              |
|:------------------|:-------------|:----------------------|:----------------|
| **id**            | UUID         | PK                    | 主键              |
| **tournament_id** | UUID         | FK → Tournament(id)   | 所属赛事            |
| **rule_id**       | UUID         | FK → Rule(id)         | 赛制规则            |
| **event_type_id** | UUID         | FK → Event_Type(id)   | 项目类型            |
| event_name        | VARCHAR(200) | NOT NULL              | 项目名称（如"男子个人佩剑"） |
| start_time        | TIMESTAMP    |                       | 项目开始时间          |
| **status_id**     | UUID         | FK → Event_Status(id) | 项目状态            |
| is_team_event     | BOOLEAN      | NOT NULL              | 是否为团体赛          |
| created_at        | TIMESTAMP    | DEFAULT NOW()         |                 |
| updated_at        | TIMESTAMP    | DEFAULT NOW()         |                 |

**索引:**

- `idx_event_tournament` (tournament_id)
- `idx_event_status` (status_id)
- `idx_event_start_time` (start_time)

---

### 1.3. Rule（赛制规则）

| 属性                        | 类型           | 约束                        | 描述       |
|:--------------------------|:-------------|:--------------------------|:---------|
| **id**                    | UUID         | PK                        | 主键       |
| rule_name                 | VARCHAR(100) | NOT NULL                  | 规则名称     |
| **elimination_type_id**   | UUID         | FK → Elimination_Type(id) | 淘汰赛类型    |
| **final_ranking_type_id** | UUID         | FK → Ranking_Type(id)     | 名次决出方式   |
| match_format              | VARCHAR(50)  |                           | 单场比赛格式   |
| pool_size                 | INTEGER      | CHECK (≥3)                | 小组赛每组人数  |
| match_duration            | INTEGER      |                           | 单局时长（秒）  |
| match_score_pool          | INTEGER      |                           | 小组赛目标分数  |
| match_score_elimination   | INTEGER      |                           | 淘汰赛目标分数  |
| total_qualified_count     | INTEGER      | NOT NULL                  | 总晋级人数    |
| group_qualification_ratio | DECIMAL(5,4) |                           | 晋级比例（备用） |
| description               | TEXT         |                           | 规则描述     |

---

## 2. 枚举与配置表

### 2.1. Tournament_Status（赛事状态）

| 属性           | 类型           | 描述               |
|:-------------|:-------------|:-----------------|
| **id**       | UUID         | PK               |
| status_code  | VARCHAR(20)  | UNIQUE, NOT NULL |
| display_name | VARCHAR(50)  | 显示名称             |
| description  | VARCHAR(200) | 描述               |

**预置数据:** `PLANNING`, `REGISTRATION_OPEN`, `REGISTRATION_CLOSED`, `ONGOING`, `COMPLETED`, `CANCELLED`

---

### 2.2. Event_Status（项目状态）

| 属性           | 类型          | 描述               |
|:-------------|:------------|:-----------------|
| **id**       | UUID        | PK               |
| status_code  | VARCHAR(20) | UNIQUE, NOT NULL |
| display_name | VARCHAR(50) |                  |

**预置数据:** `SCHEDULED`, `POOL_ROUND`, `ELIMINATION_ROUND`, `COMPLETED`, `CANCELLED`

---

### 2.3. Match_Status_Type（比赛状态）

| 属性          | 类型           | 描述               |
|:------------|:-------------|:-----------------|
| **id**      | UUID         | PK               |
| status_code | VARCHAR(20)  | UNIQUE, NOT NULL |
| description | VARCHAR(100) |                  |

**预置数据:** `SCHEDULED`, `READY`, `IN_PROGRESS`, `COMPLETED`, `FORFEITED`, `CANCELLED`, `POSTPONED`

---

### 2.4. Event_Type（项目类型）

| 属性           | 类型          | 描述                              |
|:-------------|:------------|:--------------------------------|
| **id**       | UUID        | PK                              |
| type_code    | VARCHAR(30) | UNIQUE, NOT NULL                |
| display_name | VARCHAR(50) |                                 |
| weapon_type  | VARCHAR(10) | `FOIL`, `EPEE`, `SABRE`         |
| gender       | VARCHAR(10) | `MEN`, `WOMEN`, `MIXED`, `OPEN` |

**示例:** `MEN_INDIVIDUAL_FOIL`, `WOMEN_TEAM_SABRE`

---

### 2.5. Elimination_Type（淘汰赛类型）

| 属性           | 类型          | 描述     |
|:-------------|:------------|:-------|
| **id**       | UUID        | PK     |
| type_code    | VARCHAR(30) | UNIQUE |
| display_name | VARCHAR(50) |        |

**预置数据:** `SINGLE_ELIMINATION`, `DOUBLE_ELIMINATION`, `ROUND_ROBIN_ONLY`

---

### 2.6. Ranking_Type（排名决出方式）

| 属性           | 类型          | 描述     |
|:-------------|:------------|:-------|
| **id**       | UUID        | PK     |
| type_code    | VARCHAR(30) | UNIQUE |
| display_name | VARCHAR(50) |        |

**预置数据:** `BRONZE_MATCH`, `ALL_RANKS`, `NO_THIRD_PLACE`

---

## 3. 运动员及队伍管理

### 3.1. Fencer（击剑运动员）

| 属性                 | 类型           | 约束            | 描述        |
|:-------------------|:-------------|:--------------|:----------|
| **id**             | UUID         | PK            | 主键        |
| first_name         | VARCHAR(100) | NOT NULL      | 名         |
| last_name          | VARCHAR(100) | NOT NULL      | 姓         |
| display_name       | VARCHAR(200) |               | 显示名称（姓+名） |
| gender             | VARCHAR(10)  |               | 性别        |
| country_code       | CHAR(3)      |               | ISO国家代码   |
| birth_date         | DATE         |               | 出生日期      |
| fencing_id         | VARCHAR(50)  | UNIQUE        | 国际击剑ID    |
| current_ranking    | INTEGER      |               | 当前世界排名    |
| **primary_weapon** | VARCHAR(10)  |               | 主剑种       |
| created_at         | TIMESTAMP    | DEFAULT NOW() |           |
| updated_at         | TIMESTAMP    | DEFAULT NOW() |           |

**索引:**

- `idx_fencer_country` (country_code)
- `idx_fencer_name` (last_name, first_name)
- `idx_fencer_fencing_id` (fencing_id)

---

### 3.2. Team（队伍）

| 属性           | 类型           | 约束             | 描述    |
|:-------------|:-------------|:---------------|:------|
| **id**       | UUID         | PK             | 主键    |
| **event_id** | UUID         | FK → Event(id) | 所属项目  |
| team_name    | VARCHAR(200) | NOT NULL       | 队伍名称  |
| country_code | CHAR(3)      |                | 国家/地区 |
| seed_rank    | INTEGER      |                | 种子排名  |
| created_at   | TIMESTAMP    | DEFAULT NOW()  |       |

**索引:** `idx_team_event` (event_id)

---

### 3.3. Team_Membership（队伍成员）

| 属性            | 类型      | 约束                 | 描述    |
|:--------------|:--------|:-------------------|:------|
| **team_id**   | UUID    | FK → Team(id)      |       |
| **fencer_id** | UUID    | FK → Fencer(id)    |       |
| **role_id**   | UUID    | FK → Team_Role(id) | 角色    |
| order_number  | INTEGER |                    | 出场顺序  |
| is_captain    | BOOLEAN | DEFAULT FALSE      | 是否为队长 |

**主键:** PRIMARY KEY (team_id, fencer_id)

---

### 3.4. Team_Role（队伍角色）

| 属性           | 类型          | 描述     |
|:-------------|:------------|:-------|
| **id**       | UUID        | PK     |
| role_code    | VARCHAR(20) | UNIQUE |
| display_name | VARCHAR(50) |        |

**预置数据:** `STARTER`, `SUBSTITUTE`, `RESERVE`, `CAPTAIN`

---

### 3.5. Event_Seed（项目种子排名）

| 属性               | 类型            | 约束                 | 描述   |
|:-----------------|:--------------|:-------------------|:-----|
| **event_id**     | UUID          | FK → Event(id)     |      |
| **fencer_id**    | UUID          | FK → Fencer(id)    |      |
| **seed_type_id** | UUID          | FK → Seed_Type(id) | 种子类型 |
| seed_rank        | INTEGER       | NOT NULL           | 种子排名 |
| seed_value       | DECIMAL(10,2) |                    | 种子分值 |

**主键:** PRIMARY KEY (event_id, fencer_id)

---

### 3.6. Seed_Type（种子类型）

| 属性           | 类型          | 描述     |
|:-------------|:------------|:-------|
| **id**       | UUID        | PK     |
| type_code    | VARCHAR(30) | UNIQUE |
| display_name | VARCHAR(50) |        |

**预置数据:** `WORLD_RANKING`, `NATIONAL_RANKING`, `QUALIFICATION`, `MANUAL`, `RANDOM`

---

## 4. 小组赛模型

### 4.1. Pool（小组）

| 属性           | 类型          | 约束                  | 描述          |
|:-------------|:------------|:--------------------|:------------|
| **id**       | UUID        | PK                  | 主键          |
| **event_id** | UUID        | FK → Event(id)      | 所属项目        |
| pool_number  | INTEGER     | NOT NULL            | 小组编号        |
| pool_letter  | CHAR(1)     |                     | 小组字母（A,B,C） |
| **piste_id** | UUID        | FK → Piste(id)      | 分配剑道        |
| start_time   | TIMESTAMP   |                     | 开始时间        |
| status       | VARCHAR(20) | DEFAULT 'SCHEDULED' | 状态          |
| is_completed | BOOLEAN     | DEFAULT FALSE       | 是否完成        |

**约束:** UNIQUE(event_id, pool_number)

**索引:**

- `idx_pool_event` (event_id)
- `idx_pool_piste` (piste_id)

---

### 4.2. Pool_Assignment（小组赛排名）

| 属性                 | 类型      | 约束              | 描述        |
|:-------------------|:--------|:----------------|:----------|
| **pool_id**        | UUID    | FK → Pool(id)   |           |
| **fencer_id**      | UUID    | FK → Fencer(id) |           |
| final_pool_rank    | INTEGER | NOT NULL        | 最终排名      |
| victories          | INTEGER | DEFAULT 0       | 胜场数(V)    |
| indicator          | INTEGER | DEFAULT 0       | 得失分差(Ind) |
| touches_scored     | INTEGER | DEFAULT 0       | 总得分(TS)   |
| touches_received   | INTEGER | DEFAULT 0       | 总失分(TR)   |
| matches_played     | INTEGER | DEFAULT 0       | 已赛场次      |
| is_qualified       | BOOLEAN | DEFAULT FALSE   | 是否晋级      |
| qualification_rank | INTEGER |                 | 晋级排名      |

**主键:** PRIMARY KEY (pool_id, fencer_id)

**约束:**

- UNIQUE(pool_id, final_pool_rank)
- CHECK(final_pool_rank > 0)

**索引:** `idx_pool_assignment_qualified` (pool_id, is_qualified, final_pool_rank)

---

### 4.3. Pool_Bout（小组赛单场）

| 属性                | 类型        | 约束                         | 描述   |
|:------------------|:----------|:---------------------------|:-----|
| **id**            | UUID      | PK                         | 主键   |
| **pool_id**       | UUID      | FK → Pool(id)              | 所属小组 |
| **fencer_a_id**   | UUID      | FK → Fencer(id)            | 运动员A |
| **fencer_b_id**   | UUID      | FK → Fencer(id)            | 运动员B |
| **winner_id**     | UUID      | FK → Fencer(id)            | 获胜者  |
| fencer_a_score    | INTEGER   | DEFAULT 0                  | A得分  |
| fencer_b_score    | INTEGER   | DEFAULT 0                  | B得分  |
| **status_id**     | UUID      | FK → Match_Status_Type(id) | 比赛状态 |
| scheduled_time    | TIMESTAMP |                            | 计划时间 |
| actual_start_time | TIMESTAMP |                            | 实际开始 |
| actual_end_time   | TIMESTAMP |                            | 实际结束 |
| duration_seconds  | INTEGER   |                            | 持续时间 |
| notes             | TEXT      |                            | 备注   |

**约束:**

- CHECK(fencer_a_id != fencer_b_id)
- UNIQUE(pool_id, LEAST(fencer_a_id, fencer_b_id), GREATEST(fencer_a_id, fencer_b_id))

**索引:**

- `idx_pool_bout_pool` (pool_id)
- `idx_pool_bout_status` (status_id)
- `idx_pool_bout_athletes` (fencer_a_id, fencer_b_id)

---

## 5. 个人淘汰赛模型

### 5.1. Event_Phase（项目阶段）

| 属性             | 类型          | 约束             | 描述      |
|:---------------|:------------|:---------------|:--------|
| **id**         | UUID        | PK             | 主键      |
| **event_id**   | UUID        | FK → Event(id) | 所属项目    |
| phase_code     | VARCHAR(30) | NOT NULL       | 阶段代码    |
| display_name   | VARCHAR(50) | NOT NULL       | 显示名称    |
| phase_order    | INTEGER     | NOT NULL       | 阶段顺序    |
| is_elimination | BOOLEAN     | DEFAULT TRUE   | 是否为淘汰赛  |
| target_score   | INTEGER     |                | 目标分数    |
| is_final_phase | BOOLEAN     | DEFAULT FALSE  | 是否为决赛阶段 |

**预置阶段:** `POOL`, `ROUND_64`, `ROUND_32`, `ROUND_16`, `QUARTERFINAL`, `SEMIFINAL`, `BRONZE_MATCH`, `FINAL`

**索引:** `idx_event_phase_order` (event_id, phase_order)

---

### 5.2. Match（个人淘汰赛）

| 属性                  | 类型          | 约束                         | 描述            |
|:--------------------|:------------|:---------------------------|:--------------|
| **id**              | UUID        | PK                         | 主键            |
| **event_id**        | UUID        | FK → Event(id)             | 所属项目          |
| **phase_id**        | UUID        | FK → Event_Phase(id)       | 比赛阶段          |
| **fencer_a_id**     | UUID        | FK → Fencer(id)            | 运动员A          |
| **fencer_b_id**     | UUID        | FK → Fencer(id)            | 运动员B          |
| **winner_id**       | UUID        | FK → Fencer(id)            | 获胜者           |
| fencer_a_score      | INTEGER     | DEFAULT 0                  | A得分           |
| fencer_b_score      | INTEGER     | DEFAULT 0                  | B得分           |
| match_code          | VARCHAR(20) | NOT NULL                   | 比赛编号（如M1, M2） |
| match_number        | INTEGER     |                            | 比赛序号          |
| **status_id**       | UUID        | FK → Match_Status_Type(id) | 比赛状态          |
| **piste_id**        | UUID        | FK → Piste(id)             | 比赛剑道          |
| scheduled_time      | TIMESTAMP   |                            | 计划时间          |
| actual_start_time   | TIMESTAMP   |                            | 实际开始          |
| actual_end_time     | TIMESTAMP   |                            | 实际结束          |
| duration_minutes    | INTEGER     |                            | 持续时间          |
| **forfeit_type_id** | UUID        | FK → Forfeit_Type(id)      | 退赛类型          |
| forfeit_notes       | TEXT        |                            | 退赛说明          |
| created_at          | TIMESTAMP   | DEFAULT NOW()              |               |
| updated_at          | TIMESTAMP   | DEFAULT NOW()              |               |

**约束:**

- CHECK(fencer_a_id != fencer_b_id)
- UNIQUE(event_id, match_code)

**索引:**

- `idx_match_event` (event_id)
- `idx_match_phase` (phase_id)
- `idx_match_status` (status_id)
- `idx_match_piste` (piste_id)
- `idx_match_scheduled` (scheduled_time)
- `idx_match_athletes` (fencer_a_id, fencer_b_id)

---

### 5.3. Match_Tree（个人赛晋级树）

| 属性                   | 类型          | 约束                   | 描述               |
|:---------------------|:------------|:---------------------|:-----------------|
| **current_match_id** | UUID        | FK → Match(id)       | 当前比赛（子节点）        |
| **source_match_id**  | UUID        | FK → Match(id)       | 来源比赛（父节点）        |
| **source_type_id**   | UUID        | FK → Source_Type(id) | 来源类型             |
| bracket_position     | VARCHAR(10) |                      | 位置标识（如"W1","L1"） |

**主键:** PRIMARY KEY (current_match_id, source_match_id)

**索引:** `idx_match_tree_source` (source_match_id, source_type_id)

---

### 5.4. Source_Type（来源类型）

| 属性           | 类型          | 描述     |
|:-------------|:------------|:-------|
| **id**       | UUID        | PK     |
| type_code    | VARCHAR(20) | UNIQUE |
| display_name | VARCHAR(50) |        |

**预置数据:** `WINNER`, `LOSER`, `WINNER_WINNER`, `LOSER_WINNER`, `CONSOLATION`

---

### 5.5. Forfeit_Type（退赛类型）

| 属性           | 类型          | 描述     |
|:-------------|:------------|:-------|
| **id**       | UUID        | PK     |
| type_code    | VARCHAR(30) | UNIQUE |
| display_name | VARCHAR(50) |        |

**预置数据:** `NONE`, `INJURY`, `ILLNESS`, `EQUIPMENT`, `NO_SHOW`, `DISQUALIFICATION`, `WITHDRAWAL`

---

## 6. 团体淘汰赛模型

### 6.1. Team_Match（团体淘汰赛）

| 属性                  | 类型          | 约束                         | 描述    |
|:--------------------|:------------|:---------------------------|:------|
| **id**              | UUID        | PK                         | 主键    |
| **event_id**        | UUID        | FK → Event(id)             | 所属项目  |
| **phase_id**        | UUID        | FK → Event_Phase(id)       | 比赛阶段  |
| **team_a_id**       | UUID        | FK → Team(id)              | 队伍A   |
| **team_b_id**       | UUID        | FK → Team(id)              | 队伍B   |
| **winner_team_id**  | UUID        | FK → Team(id)              | 获胜队伍  |
| team_a_score        | INTEGER     | DEFAULT 0                  | 队伍A总分 |
| team_b_score        | INTEGER     | DEFAULT 0                  | 队伍B总分 |
| match_code          | VARCHAR(20) | NOT NULL                   | 比赛编号  |
| match_number        | INTEGER     |                            | 比赛序号  |
| **status_id**       | UUID        | FK → Match_Status_Type(id) | 比赛状态  |
| **piste_id**        | UUID        | FK → Piste(id)             | 比赛剑道  |
| scheduled_time      | TIMESTAMP   |                            | 计划时间  |
| actual_start_time   | TIMESTAMP   |                            | 实际开始  |
| actual_end_time     | TIMESTAMP   |                            | 实际结束  |
| duration_minutes    | INTEGER     |                            | 持续时间  |
| **forfeit_type_id** | UUID        | FK → Forfeit_Type(id)      | 退赛类型  |
| forfeit_notes       | TEXT        |                            | 退赛说明  |
| created_at          | TIMESTAMP   | DEFAULT NOW()              |       |
| updated_at          | TIMESTAMP   | DEFAULT NOW()              |       |

**约束:** CHECK(team_a_id != team_b_id)

**索引:** 同Match表类似索引

---

### 6.2. Team_Match_Tree（团体赛晋级树）

| 属性                   | 类型          | 约束                   | 描述   |
|:---------------------|:------------|:---------------------|:-----|
| **current_match_id** | UUID        | FK → Team_Match(id)  | 当前比赛 |
| **source_match_id**  | UUID        | FK → Team_Match(id)  | 来源比赛 |
| **source_type_id**   | UUID        | FK → Source_Type(id) | 来源类型 |
| bracket_position     | VARCHAR(10) |                      | 位置标识 |

**主键:** PRIMARY KEY (current_match_id, source_match_id)

---

### 6.3. Bout（团体赛单局接力）

| 属性                | 类型        | 约束                         | 描述       |
|:------------------|:----------|:---------------------------|:---------|
| **id**            | UUID      | PK                         | 主键       |
| **team_match_id** | UUID      | FK → Team_Match(id)        | 所属团体赛    |
| bout_number       | INTEGER   | NOT NULL                   | 局次（1-9）  |
| **fencer_a_id**   | UUID      | FK → Fencer(id)            | A队上场选手   |
| **fencer_b_id**   | UUID      | FK → Fencer(id)            | B队上场选手   |
| fencer_a_score    | INTEGER   | DEFAULT 0                  | 选手A结束时比分 |
| fencer_b_score    | INTEGER   | DEFAULT 0                  | 选手B结束时比分 |
| start_score_a     | INTEGER   | DEFAULT 0                  | A队起始比分   |
| start_score_b     | INTEGER   | DEFAULT 0                  | B队起始比分   |
| target_score      | INTEGER   |                            | 本局目标分数   |
| **status_id**     | UUID      | FK → Match_Status_Type(id) | 本局状态     |
| start_time        | TIMESTAMP |                            | 开始时间     |
| end_time          | TIMESTAMP |                            | 结束时间     |
| duration_seconds  | INTEGER   |                            | 持续时间     |

**约束:**

- UNIQUE(team_match_id, bout_number)
- CHECK(bout_number BETWEEN 1 AND 9)

**索引:** `idx_bout_team_match` (team_match_id, bout_number)

---

## 7. 裁判与场地管理

### 7.1. Referee（裁判）

| 属性             | 类型           | 约束            | 描述   |
|:---------------|:-------------|:--------------|:-----|
| **id**         | UUID         | PK            | 主键   |
| first_name     | VARCHAR(100) | NOT NULL      | 名    |
| last_name      | VARCHAR(100) | NOT NULL      | 姓    |
| display_name   | VARCHAR(200) |               | 显示名称 |
| country_code   | CHAR(3)      |               | 国家代码 |
| license_number | VARCHAR(50)  | UNIQUE        | 裁判证号 |
| license_level  | VARCHAR(20)  |               | 裁判等级 |
| is_active      | BOOLEAN      | DEFAULT TRUE  | 是否活跃 |
| created_at     | TIMESTAMP    | DEFAULT NOW() |      |
| updated_at     | TIMESTAMP    | DEFAULT NOW() |      |

**索引:** `idx_referee_name` (last_name, first_name)

---

### 7.2. Match_Referee_Assignment（比赛裁判分配）

| 属性               | 类型          | 约束                    | 描述                         |
|:-----------------|:------------|:----------------------|:---------------------------|
| **id**           | UUID        | PK                    | 主键                         |
| **match_id**     | UUID        | NOT NULL              | 比赛ID                       |
| match_type       | VARCHAR(10) | NOT NULL              | 比赛类型: `INDIVIDUAL`, `TEAM` |
| **referee_id**   | UUID        | FK → Referee(id)      | 裁判                         |
| **role_id**      | UUID        | FK → Referee_Role(id) | 角色                         |
| assignment_order | INTEGER     | DEFAULT 1             | 分配顺序                       |
| assigned_at      | TIMESTAMP   | DEFAULT NOW()         | 分配时间                       |

**索引:**

- `idx_match_referee_match` (match_id, match_type)
- `idx_match_referee_referee` (referee_id)

---

### 7.3. Referee_Role（裁判角色）

| 属性           | 类型          | 描述     |
|:-------------|:------------|:-------|
| **id**       | UUID        | PK     |
| role_code    | VARCHAR(20) | UNIQUE |
| display_name | VARCHAR(50) |        |

**预置数据:** `PRESIDENT`, `SIDE_1`, `SIDE_2`, `RESERVE`, `VIDEO`

---

### 7.4. Piste（剑道）

| 属性                | 类型           | 约束                  | 描述                          |
|:------------------|:-------------|:--------------------|:----------------------------|
| **id**            | UUID         | PK                  | 主键                          |
| **tournament_id** | UUID         | FK → Tournament(id) | 所属赛事                        |
| piste_number      | VARCHAR(10)  | NOT NULL            | 剑道编号                        |
| location          | VARCHAR(100) |                     | 具体位置                        |
| piste_type        | VARCHAR(20)  |                     | 类型：`MAIN`, `SIDE`, `WARMUP` |
| is_available      | BOOLEAN      | DEFAULT TRUE        | 是否可用                        |
| notes             | TEXT         |                     | 备注                          |

**约束:** UNIQUE(tournament_id, piste_number)

**索引:** `idx_piste_tournament` (tournament_id, is_available)

---

## 8. 性能优化设计

### 8.1. 数据库分区策略（建议）

```sql
-- 按时间分区示例（PostgreSQL）
-- Tournament表按年份分区
CREATE TABLE tournament_2025 PARTITION OF tournament
    FOR VALUES FROM
(
    '2025-01-01'
) TO
(
    '2026-01-01'
);

-- Match表按赛事分区
CREATE TABLE match_event_<event_id> PARTITION OF match
    FOR VALUES IN
(
    <
    event_uuid>
);
```

### 8.2. 关键复合索引

```sql
-- 高频查询优化
CREATE INDEX idx_match_live ON match (status_id, scheduled_time) WHERE status_id IN ('IN_PROGRESS', 'SCHEDULED');

CREATE INDEX idx_pool_completion ON pool (event_id, is_completed, start_time);

-- 排名查询优化
CREATE INDEX idx_pool_ranking ON pool_assignment (pool_id, final_pool_rank DESC) INCLUDE (fencer_id, victories, indicator);
```

### 8.3. 物化视图（缓存）

```sql
-- 实时排名视图
CREATE
MATERIALIZED VIEW event_standings AS
SELECT event_id,
       fencer_id,
       RANK() OVER (PARTITION BY event_id ORDER BY total_points DESC) as current_rank
FROM (
         -- 综合小组赛和淘汰赛成绩
         ...
) WITH DATA;

-- 刷新策略：定时刷新或事件驱动刷新
```

---

## 9. 扩展功能表

### 9.1. Audit_Log（审计日志）

| 属性         | 类型           | 描述                        |
|:-----------|:-------------|:--------------------------|
| **id**     | BIGSERIAL    | 自增主键                      |
| table_name | VARCHAR(100) | 表名                        |
| record_id  | UUID         | 记录ID                      |
| operation  | VARCHAR(10)  | 操作：INSERT, UPDATE, DELETE |
| old_values | JSONB        | 旧值                        |
| new_values | JSONB        | 新值                        |
| changed_by | VARCHAR(100) | 操作者                       |
| changed_at | TIMESTAMP    | 操作时间                      |
| ip_address | INET         | IP地址                      |

**索引:** `idx_audit_table_record` (table_name, record_id, changed_at)

---

### 9.2. Notification（通知）

| 属性                | 类型           | 描述            |
|:------------------|:-------------|:--------------|
| **id**            | UUID         | PK            |
| user_id           | UUID         | 用户ID          |
| notification_type | VARCHAR(50)  | 通知类型          |
| title             | VARCHAR(200) | 标题            |
| message           | TEXT         | 内容            |
| related_id        | UUID         | 关联ID          |
| related_type      | VARCHAR(50)  | 关联类型          |
| is_read           | BOOLEAN      | DEFAULT FALSE |
| created_at        | TIMESTAMP    | DEFAULT NOW() |

**索引:** `idx_notification_user` (user_id, is_read, created_at)

---

### 9.3. Live_Score_Update（实时比分更新）

| 属性              | 类型          | 描述                       |
|:----------------|:------------|:-------------------------|
| **id**          | UUID        | PK                       |
| match_id        | UUID        | 比赛ID                     |
| match_type      | VARCHAR(10) | 比赛类型                     |
| update_type     | VARCHAR(20) | 更新类型：SCORE, STATUS, TIME |
| update_data     | JSONB       | 更新数据                     |
| sequence_number | BIGINT      | 序列号                      |
| created_at      | TIMESTAMPTZ | DEFAULT NOW()            |

**索引:** `idx_live_updates` (match_id, match_type, sequence_number DESC)

---

## 🎯 部署建议

1. **分阶段实施**：
    - 第一阶段：核心比赛表（Tournament, Event, Fencer, Match, Pool_Bout）
    - 第二阶段：晋级树、裁判、场地管理
    - 第三阶段：审计、通知、实时功能

2. **数据迁移策略**：
   ```sql
   -- 使用version字段支持渐进式升级
   ALTER TABLE tournament ADD COLUMN data_version INTEGER DEFAULT 1;
   ```

3. **API设计对应**：
    - RESTful端点按实体组织
    - GraphQL用于复杂查询（如晋级树）
    - WebSocket用于实时比分推送

4. **备份策略**：
    - 每日全量备份 + 实时WAL归档
    - 重要操作前手动快照

---

**文档版本历史：**

- v0.1: 初始设计（基础比赛结构）