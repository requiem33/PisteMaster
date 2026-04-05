# 🚀 项目名称：PisteMaster开发日志

本项目是一个基于 Django 和 Vue 的击剑编排软件。

## 📋 维护信息

* **当前版本**: v0.1.0-beta
* **状态**: 开发中 (In Progress)

---

## 🗓️ 2026-04-05

### 已完成事项

* **多实例集群开发支持**: 实现本地多节点集群测试环境
  - 添加 `DJANGO_DB_PATH` 环境变量，支持每个后端实例独立数据库
  - 添加 `VITE_PORT` 和 `VITE_API_PROXY_TARGET` 环境变量，支持多前端实例
  - 添加 `PISTEMASTER_USER_DATA_DIR` 环境变量，支持多Electron实例独立配置
  - 添加 `PISTEMASTER_API_PORT` 环境变量，指定各实例连接的后端端口
  - 修复UDP socket使用 `reuseAddr: true`，允许多实例共享同一UDP端口
  - 修复cluster-handlers使用config.apiPort而非硬编码8000
  - 更新desktop/README.md添加多实例开发文档

* **集群同步错误修复**: 修复后端集群服务的多个bug
  - 为AckQueue添加get_min_confirmed_id()方法，解决同步状态获取错误
  - 修复pending_acks属性访问，改用get_pending_count()
  - 修复is_master自动设置逻辑：仅在未明确设置时默认followerr角色

* **节点角色选择UI**: 在设置页面添加Master/Follower角色选择
  - 为ClusterConfig接口添加isMaster字段
  - 在Settings.vue添加角色选择单选按钮（Master/Follower）
  - 仅在选择Follower时显示Master IP输入框
  - 添加nodeRole中英文国际化翻译
  - 更新后端API支持is_master参数

* **is_master设置bug修复**: 修复保存Master角色后变成Follower的问题
  - 修改update_config逻辑：仅在is_master未在请求中提供时才默认false
  - 之前保存is_master=true时会因master_url/master_ip为空而被覆盖为false

* **集群状态API字段映射修复**: 修复前端获取集群状态显示undefined
  - 修复Electron端BackendClusterStatus接口使用camelCase而非snake_case
  - 后端/api/cluster/status/返回camelCase字段（nodeId, isMaster, syncLag等）
  - 合并UDP发现的peers与后端peers

* **前端获取UDP peers修复**: 修复前端显示peers始终为0
  - 在Electron环境下使用window.electron.cluster.getStatus()替代直接调用后端API
  - 将Electron的PeerInfo[]映射为前端的ClusterNode[]类型
  - 现在正确显示通过UDP发现的节点

* **UDP节点发现增强**: 添加周期性广播确保节点重发现
  - 添加announceInterval，每30秒周期性广播announce消息
  - 确保新节点加入时被发现，之前丢失的节点重新发现
  - 修复sendAnnounce中isMaster字段使用config.isMaster而非硬编码false
  - 在stop()中清理announceInterval防止内存泄漏

* **集群状态刷新修复**: 修复重置设置后集群状态不更新问题
  - 修改ClusterStatus组件在reset后调用refreshStatus()刷新状态

* **集群状态API响应修复**: 修复API响应使用camelCase字段名
  - 后端/api/cluster/status/返回camelCase格式字段

* **集群设置页面**: 实现集群模式配置UI
  - 创建Settings.vue页面，提供Mode切换、节点配置、状态显示
  - 支持UDP端口、API端口、心跳间隔、Master IP配置
  - 集成ClusterService与Electron IPC进行配置管理

### 技术决策 & 挑战

* 多实例开发需要每个组件（后端、前端、Electron）独立配置端口和数据目录
* 集群角色设置需要前后端和Electron三端协调，字段命名需一致
* UDP广播使用SO_REUSEADDR允许多进程绑定同一端口，但需要周期性广播维持发现

### 发现的问题

* 无。

---

## 🗓️ 2026-04-04

### 已完成事项

* **国际化字符串修复**: 替换硬编码中文字符串为i18n翻译
  - 修复Settings.vue、ClusterStatus.vue等组件的硬编码中文

* **Guest用户密码修复**: 设置Guest用户密码启用桌面版自动登录
  - 创建数据迁移设置Guest用户默认密码

* **桌面开发文档**: 记录Electron开发工作流和ELECTRON_RENDERER_URL配置需求

### 技术决策 & 挑战

* 无。

### 发现的问题

* 无。

---

## 🗓️ 2026-04-03

### 已完成事项

* **后端Guest用户认证**: 实现基于后端的Guest用户认证系统
  - 后端User模型添加GUEST角色
  - 创建数据迁移创建默认Guest用户（仅桌面版）
  - 添加IsSchedulerOrAdminOrGuest权限
  - 更新IsTournamentEditor和IsEventEditor支持GUEST角色
  - 允许GUEST创建比赛

* **前端Guest登录**: 实现前端Guest用户登录流程
  - 移除localStorage的本地authService
  - AuthService添加loginAsGuest()方法
  - authStore支持后端Guest登录
  - 添加GUEST角色到UserRole类型
  - UserMenu显示GUEST角色标签
  - 简化Guest用户流程

* **Dark Mode支持**: 改善前端组件的深色模式支持

* **桌面构建修复**: 移除错误的renderer配置

* **前端TypeScript修复**: 解决前端构建错误

* **后端测试修复**: 解决后端测试失败和变量遮蔽问题

### 技术决策 & 挑战

* 桌面版应用启动时自动以Guest用户登录
* Guest被视为普通用户（基于会话的认证）
* Guest可以创建/编辑自己的比赛

### 发现的问题

* 无。

---

## 🗓️ 2026-03-31

### 已完成事项

* **分布式集群架构**: 实现完整的分布式集群支持，无需中心服务器
  - Phase 1-3: 后端数据模型和同步系统
    - SyncLog和SyncState模型记录变更历史和同步状态
    - SyncManager管理变更记录和同步队列
    - AckQueue实现同步写入确认机制
  
  - Phase 4: API路由中间件
    - ApiRouterMiddleware根据节点角色路由请求
    - MasterProxy/FollowerProxy代理写请求到主节点
  
  - Phase 5: 前端同步栈
    - IndexedDBService扩展支持同步存储
    - SyncQueueService离线队列服务
    - ConflictResolver冲突解决
    - NetworkService网络状态监控
    - ClusterService集群协调
  
  - Phase 6: Electron集成
    - UDP广播服务用于节点发现
    - IPC处理器暴露集群API
    - 集群配置管理
  
  - Phase 7: UI组件
    - ClusterStatus组件显示集群状态
    - SyncProgress同步进度指示器
    - ConflictReview冲突解决面板
    - 中英文国际化支持

* **测试和文档**: Phase 8完成
  - 单元测试: BullyElection算法测试
  - 集成测试: SyncManager和AckQueue测试
  - E2E测试: 多节点场景、选举、故障转移测试
  - 部署指南: `docs/deployment/cluster-setup.md`
  - 故障排查: `docs/deployment/troubleshooting.md`

### 技术决策 & 挑战

* **选举算法**: 使用Bully算法，节点ID决定优先级，高ID节点成为主节点
* **数据同步**: 主节点记录所有写操作到SyncLog，从节点拉取并应用
* **冲突解决**: 版本号+时间戳双保险，关键数据需人工审核
* **离线支持**: 前端维护离线队列，网络恢复后自动同步

### 发现的问题

* 无。

## 🗓️ 2026-03-30

### 已完成事项

* **用户认证系统**: 实现完整的用户认证和角色权限控制
  - 自定义User模型，支持ADMIN和SCHEDULER两种角色
  - 认证API端点: login、logout、me
  - 权限类: IsAdmin、IsSchedulerOrAdmin、IsTournamentEditor、IsEventEditor
  - 前端auth store、authService服务和登录页面
  - UserMenu组件集成到AppHeader
  - 桌面版本地auth service支持guest模式
  - 数据迁移创建默认admin用户 (admin/admin)

* **Tournament权限控制**: 扩展Tournament模型支持用户关联
  - Tournament模型新增created_by和schedulers字段
  - Tournament域模型同步新增created_by_id和scheduler_ids字段
  - TournamentMapper处理用户字段转换
  - IsTournamentEditor权限使用域模型字段
  - IsEventEditor权限控制Event级别操作
  - Django Admin显示User模型和Tournament用户字段

* **Bug修复**: 多个代码质量问题
  - 修复permissions.py重复类定义
  - 修复pre-commit hook使用`git rev-parse --show-toplevel`定位项目根目录
  - 修复TypeScript编译错误: router导航守卫未使用参数、authService类型不匹配

### 技术决策 & 挑战

* 桌面版支持离线使用，提供guest模式绕过认证
* 权限设计: 管理员可创建比赛，编排员可编辑分配给自己的比赛
* 域模型与ORM模型分离，Service层处理created_by_id转换

### 发现的问题

* 无。

---

## 🗓️ 2026-03-26

### 已完成事项

* **Docker CI/CD修复**: 修复GitHub Actions构建流程
  - 添加前端Dockerfile (`web_frontend/Dockerfile`)
  - 配置.dockerignore排除不必要文件
  - 修复Docker构建警告和GHCR权限错误
  - 使用DOCKER_ACCESS_TOKEN密钥进行Docker Hub登录

* **Pre-commit Hooks**: 添加本地lint检查，与GitHub Actions CI保持一致
  - 创建 `scripts/pre-commit.sh` 脚本，运行前端ESLint和Python flake8/black检查
  - 创建 `scripts/setup-hooks.sh` 脚本，安装pre-commit git hook
  - 支持自动检测 `venv/` 和 `.venv/` 虚拟环境
  - 排除 `dist/` 构建产物目录
  - 更新 `AGENTS.md` 添加使用文档

### 技术决策 & 挑战

* 使用脚本直接调用 `venv/bin/flake8` 而非激活虚拟环境，避免 `deactivate` 在失败时不执行的问题
* Git hooks运行在 `.git/` 目录，脚本需自动定位项目根目录

### 发现的问题

* 无。

---

## 🗓️ 2026-03-24

### 已完成事项

* **CI测试配置**: 配置pytest和vitest用于CI测试
  - 添加pytest配置，支持Django测试运行
  - 配置vitest用于前端单元测试
  - 创建可复用的CI工作流

* **代码规范化**: 解决所有linting错误
  - **Black格式化**: 升级到Black 26并固定版本，解决Python格式化问题
  - **flake8**: 配置.flake8文件，移除内联注释，解决所有Python linting错误
  - **ESLint**: 解决前端代码linting错误，应用格式化

* **依赖管理**: 清理未使用的包和修复安全漏洞
  - 移除未使用的npm依赖
  - 解决安全漏洞

* **文档更新**: 更新AGENTS.md反映当前技术栈
  - 更新桌面应用架构说明
  - 添加AGENTS.md到版本控制

### 技术决策 & 挑战

* Black 26格式化规则变更，需要固定版本以保持一致性
* CI工作流需要可复用以支持多个构建目标

### 发现的问题

* 无。

---

## 🗓️ 2026-03-23

### 已完成事项

* **GitHub Actions工作流修复**: 多项CI/CD配置问题
  - 更新Python版本到3.12以兼容项目依赖
  - 更新Node.js版本到22以兼容electron-builder
  - 配置Node.js 24选项支持
  - 修正GitHub workflow配置问题

* **桌面应用构建修复**: 解决Electron桌面版构建问题
  - 配置Electron使用预构建前端
  - 使用相对路径确保桌面应用兼容性
  - 添加生产环境配置文件用于桌面API URL
  - 解决桌面应用启动问题

* **TypeScript错误修复**: 解决前端类型错误
  - 移除未使用的依赖
  - 应用ESLint格式化

### 技术决策 & 挑战

* Electron-builder需要Node.js 22+支持
* 桌面应用需要相对路径和预构建前端，避免开发服务器依赖
* 生产环境API URL需要独立配置文件

### 发现的问题

* 无。

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
