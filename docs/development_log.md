# 🚀 项目名称：PisteMaster开发日志

本项目是一个基于 Django 和 Vue 的击剑编排软件。

## 📋 维护信息

* **当前版本**: v0.1.0-beta
* **状态**: 开发中 (In Progress)

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
