# 深圳市积水监测系统工程总览

本文档说明深圳市积水监测系统的整体工程安排，帮助快速理解项目目标、主线流程、技术架构、目录组织、阶段计划和后续扩展边界。

## 1. 项目目标

本项目目标是建设一套深圳市积水监测系统，实时接入水位监测数据，并在地图上展示全市积水情况，为城市防汛和应急指挥提供支撑。

系统需要回答以下核心问题：

- 哪里出现积水或积水风险。
- 当前水位和风险等级是什么。
- 水位是否正在上升、下降或波动。
- 哪些点位或行政区需要重点关注。
- 数据是否及时、可信、可追溯。
- 未来短时风险趋势如何，是否需要提前研判。

因此，本项目不是单纯做一个地图页面，而是围绕“数据接入、数据治理、风险研判、预测辅助、地图展示、统计查询”的完整主线建设一套可运行、可演示、可扩展的积水监测系统。

## 2. 工程主线

项目主线如下：

```text
实时水位数据接入
-> 原始数据归档
-> SQLite 入库
-> 数据质量检查
-> 点位坐标校核
-> 风险等级和趋势计算
-> 轻量预测模型
-> FastAPI 主线接口
-> Vue + 高德地图展示
-> 统计、历史查询、预测结果和数据状态
```

主线交付重点：

- 能从开放数据或本地归档数据获取水位数据。
- 能保存原始数据，保证数据可追溯。
- 能将水位数据导入本地 SQLite。
- 能处理空水位、重复记录和导入批次状态。
- 能通过坐标候选和人工校核确定地图落点。
- 能计算风险等级、趋势和轻量预测结果。
- 能通过 FastAPI 提供地图、统计、历史、校核、预测和数据状态接口。
- 能通过 Vue + 高德地图展示全市积水态势。

## 3. 主线模块

### 3.1 数据接入与归档

数据接入模块负责从深圳开放数据平台或本地归档文件获取水位数据。

主要输入：

- 市水务局积涝点水位数据。
- 市水务局测站基本信息表。
- 已下载 CSV 和原始分页 JSON。

主要输出：

- 原始分页 JSON。
- 汇总 CSV。
- 下载元数据。
- 数据下载流程说明。

工程要求：

- 原始数据必须保留在 `download/`。
- 不只保留清洗后的结果。
- 每次下载和导入都要能追溯来源。

### 3.2 SQLite 数据底座

当前阶段优先使用 SQLite 完成主线闭环。

SQLite 的作用：

- 快速验证水位数据导入。
- 支撑风险计算和趋势计算。
- 支撑地图点位、统计、历史查询和数据状态接口。
- 降低早期环境复杂度。

本地数据库位置：

```text
data/local/shenzhen_water.db
```

后续可在主线稳定后迁移到 PostgreSQL + PostGIS。

### 3.3 数据质量检查

数据质量检查用于保证地图和统计结果可信。

当前重点口径：

- 空水位保留在原始层和历史明细中，但不参与风险计算。
- 完全重复 ID 不重复进入业务统计。
- 月份统计应使用 `observed_at` 的真实日期。
- 导入批次需要记录成功、失败、行数和错误信息。
- 数据状态页面需要展示数据是否及时、是否导入成功。

### 3.4 坐标校核

测站基础信息缺少经纬度，因此地图展示不能直接编造坐标。

坐标校核流程：

```text
点位名称或地址
-> 高德地理编码候选
-> 候选坐标列表
-> 人工审核
-> 审核通过坐标
-> 地图展示
```

地图只展示审核通过的点位。

### 3.5 风险、趋势和预测模型

风险和预测是防汛研判主线的一部分。

当前阶段先实现轻量方案：

- 风险等级：基于统一阈值计算正常、关注、警戒、危险、无数据。
- 趋势指标：基于最近若干条有效水位计算上升、下降、稳定、波动、无数据。
- 预测模型：先采用规则型或轻量预测，根据历史水位、当前水位、趋势和数据新鲜度生成未来短时风险等级或趋势提示。

当前不做复杂机器学习训练，但必须保留预测结果展示能力。

预测结果应包含：

- 点位 ID。
- 预测目标时间。
- 预测风险等级。
- 预测趋势。
- 置信度。
- 规则或模型版本。
- 生成时间。

### 3.6 后端主线接口

后端采用 FastAPI。

主线 API 包括：

| API | 用途 |
|---|---|
| `GET /api/map/points` | 地图点位、最新水位、风险等级、趋势 |
| `GET /api/map/districts` | 深圳行政区边界 |
| `GET /api/stats/overview` | 全市风险统计 |
| `GET /api/stats/districts` | 行政区风险统计 |
| `GET /api/points/{id}/history` | 单点历史水位 |
| `POST /api/locations/geocode-candidates` | 生成坐标候选 |
| `POST /api/locations/{id}/review` | 审核点位坐标 |
| `GET /api/predictions` | 查询预测结果 |
| `GET /api/imports/latest` | 最近导入批次和数据状态 |

### 3.7 前端主线页面

前端采用 Vue + 高德 JS API。

主线页面包括：

| 页面 | 作用 |
|---|---|
| 指挥地图首页 | 展示全市积水点位、风险颜色、行政区边界、态势统计 |
| 历史查询页 | 查询单点历史水位和水位变化 |
| 点位校核页 | 审核坐标候选，确认地图落点 |
| 预测结果页 | 展示未来风险等级、预测趋势、模型版本和生成时间 |
| 数据状态页 | 展示数据源、导入批次、成功失败状态和错误信息 |

地图弹窗应展示：

- 点位名称。
- 当前水位。
- 风险等级。
- 趋势。
- 观测时间。
- 所属行政区。
- 预测风险摘要。
- 历史曲线入口。

## 4. 支线和后续扩展

以下能力属于支线或后续增强，不阻塞当前主线交付：

- 告警中心。
- 用户、角色和审计日志。
- 处置工单。
- 真实短信、电话或第三方推送。
- 多部门协同流程。
- 细粒度权限控制。
- PostgreSQL + PostGIS 迁移。
- 后端调度任务。
- 点位级阈值。
- 降雨、道路、历史易涝点扩展图层。

这些能力可以先保留设计和接口位置，等主线稳定后逐步实现。

## 5. 技术架构

当前技术路线：

| 层级 | 技术或目录 | 说明 |
|---|---|---|
| 数据采集 | Python 脚本 | 下载开放数据、归档 JSON/CSV |
| 数据存储 | SQLite | 当前主线数据库 |
| 后端服务 | FastAPI | 提供地图、统计、历史、校核、预测和数据状态接口 |
| 前端应用 | Vue | 展示指挥地图和后台主线页面 |
| 地图能力 | 高德 JS API | 地图底图、Marker、行政区边界、地理编码 |
| 后续空间能力 | PostgreSQL + PostGIS | 后续支持空间查询和扩展图层 |

系统分层：

```text
数据源层
-> 数据采集与处理层
-> 数据存储层
-> FastAPI 服务层
-> Vue + 高德地图应用层
```

## 6. 当前目录安排

当前项目目录：

```text
.
├── task.md
├── PROJECT_OVERVIEW.md
├── PROJECT_STRUCTURE.md
├── data/
├── docs/
├── download/
├── scripts/
└── tests/
```

核心文件和目录职责：

| 文件或目录 | 作用 |
|---|---|
| `task.md` | 原始需求说明 |
| `PROJECT_OVERVIEW.md` | 工程整体目标、主线流程和安排 |
| `PROJECT_STRUCTURE.md` | 目录结构和文件职责说明 |
| `data/local/` | 本地 SQLite 数据库 |
| `data/raw_samples/` | 样本页面或样本响应 |
| `download/` | 原始数据下载归档 |
| `scripts/` | 数据下载、导入、检查脚本 |
| `tests/` | 自动化测试 |
| `docs/data_reference.md` | 数据源、字段和缺口说明 |
| `docs/data_quality_report.md` | 已下载数据质量审计报告 |
| `docs/superpowers/specs/` | 系统设计文档 |
| `docs/superpowers/plans/` | 排期和计划文档 |

## 7. 后续工程目录

进入代码实现后，建议新增：

```text
backend/
frontend/
data/geo/
docs/api_reference.md
docs/database.md
docs/deployment.md
docs/user_guide.md
```

### 7.1 后端目录

```text
backend/
  app/
    main.py
    core/
      config.py
      database.py
    api/
      routes_map.py
      routes_points.py
      routes_stats.py
      routes_locations.py
      routes_imports.py
      routes_predictions.py
    models/
    schemas/
    services/
    repositories/
    tasks/
  tests/
  pyproject.toml
```

后端优先实现：

- 健康检查。
- 数据库连接。
- 地图点位接口。
- 统计接口。
- 历史水位接口。
- 坐标候选和审核接口。
- 预测结果接口。
- 数据状态接口。

### 7.2 前端目录

```text
frontend/
  src/
    main.ts
    router/
    api/
      map.ts
      points.ts
      stats.ts
      locations.ts
      predictions.ts
      imports.ts
    map/
      MapProvider.ts
      AMapProvider.ts
    views/
      CommandMap.vue
      HistoryQuery.vue
      LocationReview.vue
      PredictionResults.vue
      DataStatus.vue
    components/
      RiskSummaryPanel.vue
      DistrictStatsPanel.vue
      HighRiskList.vue
      PointPopup.vue
      WaterLevelChart.vue
    stores/
```

前端优先实现：

- 指挥地图首页。
- 风险统计面板。
- 点位弹窗。
- 历史水位曲线。
- 坐标校核页面。
- 预测结果页面。
- 数据状态页面。

## 8. 阶段安排

### 阶段 1：需求冻结与工程准备

时间：2026-06-23 至 2026-06-25

目标：

- 明确主线和支线边界。
- 完成顶层设计和排期。
- 确认目录结构、运行环境和关键依赖。

### 阶段 2：数据底座与后端基础

时间：2026-06-26 至 2026-07-01

目标：

- 梳理开放数据接口和字段。
- 完成 SQLite 数据导入。
- 完成风险和趋势计算。
- 搭建 FastAPI 基础接口。

### 阶段 3：前端地图闭环

时间：2026-07-02 至 2026-07-04

目标：

- 搭建 Vue 项目。
- 初始化高德地图。
- 展示积涝点、行政区边界、风险颜色和点位弹窗。
- 联通统计、历史查询、坐标校核和数据状态页面。

### 阶段 4：主线加固与预测能力

时间：2026-07-05 至 2026-07-10

目标：

- 加固数据模型和数据质量口径。
- 完善风险和趋势规则。
- 实现轻量预测模型和预测结果接口。
- 在地图弹窗或预测结果页展示预测摘要。

### 阶段 5：文档、演示和交付准备

时间：2026-07-11 至 2026-07-14

目标：

- 完善主线页面。
- 整理接口说明、数据库说明和部署运行说明。
- 准备演示数据、预测样例和演示脚本。

### 阶段 6：联调、测试与验收

时间：2026-07-15 至 2026-07-17

目标：

- 联调数据采集、SQLite、FastAPI、Vue、高德地图和预测展示。
- 执行接口测试、数据校验和前端流程测试。
- 整理最终演示版本、测试记录和验收清单。

## 9. 当前已有成果

当前已有：

- 原始需求：`task.md`。
- 工程目录说明：`PROJECT_STRUCTURE.md`。
- 数据源说明：`docs/data_reference.md`。
- 数据质量报告：`docs/data_quality_report.md`。
- 顶层设计：`docs/superpowers/specs/2026-06-23-shenzhen-flood-monitoring-design.md`。
- 25 天排期：`docs/superpowers/plans/2026-06-23-shenzhen-flood-monitoring-25-day-schedule.md`。
- 本地 SQLite 数据库：`data/local/shenzhen_water.db`。
- 数据下载脚本：`scripts/download_flood_water_levels.py`。
- SQLite 导入脚本：`scripts/import_water_levels_sqlite.py`。
- 数据库检查脚本：`scripts/check_local_database.py`。
- 脚本测试：`tests/`。

## 10. 下一步工作

近期优先事项：

1. 完成 Day 3 工程准备：确认 `backend/`、`frontend/`、`data/geo/`、`docs/` 的落地结构。
2. 确认 Python、Node、SQLite、高德 Key 等环境准备事项。
3. 复核数据源字段和质量口径。
4. 加固 SQLite 表结构和导入脚本。
5. 搭建 FastAPI 主线接口骨架。
6. 搭建 Vue + 高德地图主页面。
7. 实现风险、趋势和轻量预测结果展示。

## 11. 汇报脉络

对项目导师说明时，可以按以下顺序讲：

```text
项目目标
-> 主线流程
-> 数据和目录现状
-> 技术架构
-> 核心模块
-> 支线边界
-> 25 天阶段安排
-> 当前成果
-> 下一步计划
```

一句话总结：

```text
本项目先完成“实时水位数据接入、风险与预测研判、地图展示、统计查询、数据状态”的主线闭环，再逐步扩展告警、审计、工单和空间图层等支线能力。
```
