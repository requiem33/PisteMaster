# 🚀 项目名称：PisteMaster开发日志

本项目是一个基于 Django 和 Vue 的击剑编排软件。

## 📋 维护信息

* **当前版本**: v0.1.0-beta
* **状态**: 开发中 (In Progress)

---

## 🗓️ 2026-03-16

### 已完成事项

* **最终排名显示修复**: 修复FinalRanking组件排名显示错误
  - **问题1: 过期props数据** - FinalRanking依赖父组件传递的eventInfo，但导航到FinalRanking时父组件未刷新，导致live_ranking为空
  - **修复**: 添加onMounted钩子，组件挂载时主动从后端获取最新事件数据
  
  - **问题2: maxStageIndex计算错误** - 使用stages.length计算maxStageIndex，但stages数组不包含seeding阶段(索引0)，导致所有选手finalStageIndex被错误限制为0或1
  - **修复**: 从实际排名数据计算maxStageIndex，遍历所有选手找出最大阶段索引
  
  - **问题3: ID类型不匹配** - updateStageRanking中Map查找时，stageResults的ID与live_ranking的ID类型不一致导致查找失败
  - **修复**: 使用String()确保ID类型一致性

* **PoolRanking修复**: 传递eventId到getEventPoolRanking
  - 修复PoolRanking组件无法获取排名数据的问题

* **Pool域模型同步**: 同步Pool域模型与Django ORM模型
  - Django模型新增 `fencer_b` 和 `score_b` 字段用于存储对手信息
  - 域模型 `Pool` 和 `PoolAssignment` 新增对应字段并更新mapper
  - 支持 `fencer_b` 为null的情况（轮空选手）

### 技术决策 & 挑战

* 组件数据源策略：FinalRanking组件在onMounted时主动获取数据，而非完全依赖props，避免父组件状态未同步的问题
* 阶段索引计算：排名数据使用0=seeding, 1=pool, 2=DE的索引体系，而stages数组仅包含pool和DE，需从实际数据计算最大索引
* 域模型与ORM模型分离：Pool域模型设计为独立于Django ORM，通过Mapper层转换，便于未来更换持久层或支持离线模式。Django ORM新增字段时需同步更新域模型和Mapper

### 发现的问题

* 无。

---

## 🗓️ 2026-03-15

### 已完成事项 (Completed)

* **数据同步架构**: 实现IndexedDB与后端数据库的完整同步
  - 新增 `syncEventToLocal()` 方法，在事件更新后同步到本地缓存
  - `saveFencers()` → 同步到 IndexedDB
  - `syncEventFencers()` → 同步选手-项目关联到 IndexedDB
  - `initializeLiveRanking()` → 同步事件到 IndexedDB
  - `updateLiveRanking()` → 同步事件到 IndexedDB
  - `updateEvent()` → 同步事件到 IndexedDB
  - `savePools()` → 同步分组到 IndexedDB
  - `updatePoolResults()` → 同新分组结果到 IndexedDB
  - IndexedDB版本从5升级到6
  - 新增批量保存方法：`saveFencers()`, `savePools()`, `saveEventFencerLinks()`
  - 错误处理策略：记录错误但继续执行（后端为事实来源）

* **自定义规则持久化修复**: 修复自定义规则未保存到数据库的问题
  - `Event` 域模型新增 `custom_rule_config` 字段
  - `EventMapper` 新增 `custom_rule_config` 映射
  - `EventService.create_event()` 传递 `custom_rule_config`
  - Django Admin 显示 `custom_rule_config` 和 `stages_config`

* **PoolScoring渲染修复**: 修复计分表渲染错误
  - 验证 `results` 和 `stats` 数组维度匹配当前选手数量
  - 解决 `Cannot read properties of undefined (reading '1')` 错误

### 技术决策 & 挑战

* IndexedDB同步策略：后端更新成功后同步到本地缓存，为未来多客户端架构做准备
* 数据一致性：后端为事实来源，IndexedDB作为离线缓存

### 发现的问题 (Known Issues)

* 无。

---

## 🗓️ 2026-03-14

### 已完成事项 (Completed)

* **Bug修复**: 多个前后端数据流问题
  - 修复 `EventOrchestrator` 使用 `tournament_info.id` 代替 `tournament_id`
  - 修复 `getFencersByEvent` 使用 `fencer_info` 代替 `fencer` 字段
  - 修复 `bulk-save` API URL 路径（下划线改连字符）
  - 修复 `start_time` 字段在 `DataManager.ts` 和 `EventCreateSerializer` 中缺失

### 技术决策 & 挑战

* 无。

### 发现的问题 (Known Issues)

* 无。

---

## 🗓️ 2026-03-12

### 已完成事项 (Completed)

* **CSRF Token处理**: 前端API请求添加CSRF token支持
  - `DataManager.ts` 新增 `getCsrfToken()` 函数
  - 所有POST/PUT/DELETE请求自动携带 `X-CSRFToken` header

* **SerializerMethodField修复**: 修复dataclass域模型的序列化问题
  - `DomainModelSerializer.to_representation()` 正确处理 `SerializerMethodField`

### 技术决策 & 挑战

* 无。

### 发现的问题 (Known Issues)

* 无。

---

## 🗓️ 2026-03-11

### 已完成事项 (Completed)

* **后端架构重构**: 实现Clean Architecture模式
  - 创建 `DomainModelSerializer` 基类，支持ORM和dataclass域模型
  - 创建域模型分页工具 `paginate_domain_models`
  - 所有ViewSet统一使用 `GenericViewSet`，数据流经过Service层
  - 所有Serializer继承 `DomainModelSerializer`
  - 移除Service层重复验证逻辑，验证统一在Serializer

* **规则系统重构**: 实现预设规则与自定义规则
  - `DjangoRule` 新增 `stages_config`, `is_preset`, `preset_code` 字段
  - `DjangoEvent` 新增 `custom_rule_config` 字段
  - 数据迁移：预置 World Cup 和 Olympics 规则
  - API `/rules/` 仅返回预设规则 (`is_preset=True`)
  - 自定义规则存储在Event中，不可复用

* **前端规则选择**: 支持预设规则和自定义规则
  - `EventForm.vue` 新增规则模式选择（预设/自定义）
  - 从API加载预设规则列表
  - 预设规则显示阶段预览（只读）
  - 自定义规则使用 `RuleSettings.vue` 配置

* **Bug修复**: EventOrchestrator阶段显示问题
  - 修复 `rule_info.stages` 为空的fallback逻辑
  - API返回完整的 `rule_info` 包含 `stages`

### 技术决策 & 挑战

* 规则存储策略：预设规则存在 `DjangoRule` 表，自定义规则存在 `DjangoEvent.custom_rule_config`
* 规则解析优先级：`custom_rule_config.stages` > `rule.stages_config` > 默认World Cup

### 发现的问题 (Known Issues)

* 无。

---

## 🗓️ 2026-01-12

### 已完成事项 (Completed)

* **web前端**: 已打通个人赛完整流程。

### 技术决策 & 挑战

* 单项比赛（Event）需要先选择/自定义规则，再根据规则，动态生成编排页面。

### 发现的问题 (Known Issues)

* 无。

---

## 🗓️ 2025-12-21

### 已完成事项 (Completed)

* **web前端**: 完成国际化框架设计。提取出header组件AppHeader.vue。

### 技术决策 & 挑战

* 无。

### 发现的问题 (Known Issues)

* 无。

---

## 🗓️ 2025-12-20

### 已完成事项 (Completed)

* **web前端**: 完成前端编排流程的基本页面设计。

### 技术决策 & 挑战

* 需要支持离线、在线版本。离线版本，编排数据保存在IndexedDB；在线版本，数据直接存入后端数据库。

### 发现的问题 (Known Issues)

* 无。

---
