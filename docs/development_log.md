# 🚀 项目名称：PisteMaster开发日志

本项目是一个基于 Django 和 Vue 的击剑编排软件。

## 📋 维护信息

* **当前版本**: v0.1.0-beta
* **状态**: 开发中 (In Progress)

---

## 🗓️ 2026-03-19

### 已完成事项

* **Electron桌面版构建与测试**: 完成Windows桌面版打包和测试
  - 构建`PisteMaster-Setup-0.1.0.exe`安装程序
  - 构建`win-unpacked/`便携版
  - 验证应用启动、创建比赛、卸载数据持久化
  - **重要发现**: Windows需要开启开发者模式才能运行electron-builder（symlink权限问题）
  - 用户数据存储在`%APPDATA%/PisteMaster/data/`，卸载后保留
  - 更新缓存存储在`%APPDATA%/pistemaster-desktop-updater/`

* **Web版Docker部署**: 完成Docker容器化部署架构
  - 创建`docker-compose.yml`编排PostgreSQL + Django + nginx
  - 创建`backend/Dockerfile`构建Django镜像
  - 创建`backend/requirements-docker.txt`定义Docker依赖（psycopg2-binary）
  - 创建`nginx.conf`配置反向代理和静态文件服务
  - 创建`.env.docker`环境变量模板

* **跨域API修复**: 解决前后端分离部署的CORS和CSRF问题
  - 创建`CsrfExemptSessionAuthentication`认证类，免除API端点的CSRF检查
  - 配置`CORS_ALLOW_ALL_ORIGINS`支持动态IP访问
  - 配置`CSRF_TRUSTED_ORIGINS`包含WSL和localhost地址
  - 修复`DataManager.ts`使用动态API_BASE_URL环境变量

* **构建文档**: 创建`docs/BUILD.md`
  - 桌面版构建完整流程（开发者模式、依赖安装、打包命令）
  - Web版Docker部署流程（容器启动、数据库初始化、WSL网络配置）
  - 开发模式运行指南
  - 常见问题排查（symlink权限、CORS、CSRF、端口冲突）
  - 架构图示和快速命令参考

### 技术决策 & 挑战

* **开发者模式要求**: electron-builder下载的winCodeSign包含macOS符号链接，Windows创建symlink需要开发者模式或管理员权限
* **Docker网络**: WSL2与Windows浏览器网络隔离，需通过WSL IP地址访问容器
* **CSRF策略**: API-only后端使用跨域请求，传统SessionAuthentication的CSRF cookie机制不适用，创建CSRF-exempt认证类
* **nginx代理**: 前端访问`/api/*`由nginx代理到Django后端，避免浏览器直接访问后端端口

### 发现的问题

* electron-updater缓存(~97MB)在用户数据目录保留，可考虑在卸载时清理
* 生产环境应使用正式SECRET_KEY和HTTPS

---

## 🗓️ 2026-03-17

### 已完成事项

* **Electron桌面应用架构搭建**: 创建完整的Electron桌面项目结构
  - 创建`desktop/`目录，删除旧的`desktop_app/`
  - 配置electron-vite构建系统
  - 配置electron-builder打包配置
  - 添加Vue依赖到desktop/package.json
  - 配置.npmrc支持中国镜像下载Electron

* **Django设置分离**: 重构Django settings为模块化结构
  - `settings/base.py` - 通用配置
  - `settings/development.py` - 开发环境(SQLite)
  - `settings/production.py` - 生产环境(PostgreSQL)
  - `settings/desktop.py` - 桌面版(SQLite in%APPDATA%)
  - 入口`settings.py`通过环境变量`DJANGO_SETTINGS_MODULE`选择配置

* **PyInstaller配置优化**: 修复Python后端打包问题
  - 添加所有hidden imports到PisteMaster.spec
  - 修复`runserver --noreload`参数(原`--nothreading`不够)
  - 创建`run_desktop.py`作为打包入口
  - 验证`pistemaster-backend.exe`可独立运行

* **GitHub Actions CI/CD**: 添加自动化构建流水线
  - `.github/workflows/build-desktop.yml` - 桌面版构建
  - `.github/workflows/build-web.yml` - Web版构建
  - `.github/workflows/release.yml` - 发布流程
  - `scripts/build-python.ps1/sh` - Python打包脚本

* **Electron桌面应用修复**: 修复模块加载和路由问题
  - **问题1: electron-updater模块加载失败** - 打包后的应用启动时报"Cannot find module"错误
  - **修复**: 将`electron-updater`从静态import改为动态`await import()`，延迟加载避免模块初始化时序问题
  
  - **问题2: Vue前端空白页** - Electron加载file://协议时Vue Router的createWebHistory不工作
  - **修复**: 改用createWebHashHistory()，兼容file://协议和http://协议
  
  - **问题3: 图标文件损坏** - 原icon.png文件损坏导致electron-builder报错
  - **修复**: 创建256x256有效PNG图标，移动到resources/目录

* **Python后端打包验证**: 确认PyInstaller打包正常工作
  - `pistemaster-backend.exe` 启动成功
  - Django migrations正常执行
  - 服务器在http://127.0.0.1:8000运行

* **文档更新**: 完善构建文档
  - 更新`docs/MVP_BUILD_PLAN.md`添加monorepo迁移计划
  - 更新`desktop/README.md`添加Electron镜像配置说明
  - 更新`.gitignore`忽略构建产物

### 技术决策 & 挑战

* **Python 3.14兼容性**: 系统Python 3.14移除了`pkgutil.find_loader`，改用现有venv(Python 3.12)
* **PyInstaller --noreload**: Django开发服务器在frozen executable中需要`--noreload`参数
* **Electron镜像**: 中国网络环境需要配置`ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"`
* **动态模块加载**: electron-updater依赖链复杂，在ASAR包中静态import会失败。使用动态import()在app.whenReady()后加载，确保Electron环境初始化完成
* **Vue Router模式**: createWebHistory需要服务器端路由支持，file://协议无法使用。createWebHashHistory使用#锚点路由，兼容所有协议
* **electron-vite配置**: externalizeDepsPlugin()正确打包主进程依赖，但需要处理运行时动态加载的模块

### 发现的问题

* electron-updater的依赖debug模块在ASAR中路径解析可能仍有问题，但已通过try-catch处理为非致命错误

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
