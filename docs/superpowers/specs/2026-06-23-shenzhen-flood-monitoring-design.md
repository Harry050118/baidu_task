# 深圳市积水实时监测地图系统顶层设计

## 1. 项目定位

本项目建设一套深圳市积水实时监测地图系统，主要服务城市防汛和应急指挥。系统将积涝点水位数据、监测点信息、点位坐标、风险等级、行政区边界等信息整合到高德地图上，帮助指挥人员快速判断全市积水态势。

系统需要回答以下核心问题：

- 哪里发生积水或存在积水风险。
- 当前风险等级是什么。
- 水位是否持续上升。
- 风险点集中在哪些行政区。
- 数据是否及时、可信、可追溯。

项目不应只设计为一个地图展示页面，而应设计为数据驱动的城市积水监测指挥系统：数据可信、点位可校核、风险可解释、地图可交互、历史可追溯、未来可扩展。

## 2. 建设边界

### 2.1 一期范围

一期采用分阶段演进路线，优先打通可演示、可扩展的主链路：

```text
开放数据采集 -> 原始数据归档 -> 数据入库 -> 点位坐标校核 -> 风险等级计算 -> 高德地图展示 -> 统计与历史查询
```

一期包括：

- 深圳开放数据平台积涝点水位数据采集。
- 测站/积涝点基础信息管理。
- 高德地理编码候选坐标生成。
- 人工审核点位坐标，审核通过后进入正式地图展示。
- 统一规则风险等级计算。
- 点位最新水位状态快照。
- 深圳行政区边界展示。
- 指挥地图首页。
- 历史水位查询。
- 数据源导入状态查看。

### 2.2 一期不做或仅预留

以下能力放入二期，避免一期范围过大：

- 实时数据流接入。
- 告警推送。
- 处置工单闭环。
- 多角色登录权限。
- 降雨图层。
- 道路图层。
- 历史易涝点图层。
- 复杂机器学习预测。

预测模型在架构中预留模块位置。一期只展示简单趋势指标，例如持续上升、持续下降、波动、无数据。

## 3. 总体架构

系统采用前后端分离架构：

- 后端：FastAPI。
- 前端：Vue。
- 地图：高德 JS API。
- 一期数据库：SQLite，用于快速验证现有数据链路。
- 正式目标数据库：PostgreSQL + PostGIS。
- 数据采集：延续现有 Python 脚本，后续纳入后端任务调度。

系统分为五层。

### 3.1 数据源层

数据源包括：

- 市水务局积涝点水位数据。
- 市水务局测站基本信息表。
- 深圳行政区 GeoJSON。
- 高德地理编码服务。

当前项目已确认测站基础信息表缺少经纬度，因此不能编造测站坐标。点位坐标采用混合方案：先通过高德地理编码生成候选坐标，再由人工审核确认。只有审核通过的点位进入正式地图展示。

### 3.2 数据处理层

数据处理层负责：

- 定时或手动拉取开放数据。
- 保存原始分页 JSON。
- 汇总 CSV。
- 清洗并导入数据库。
- 计算点位最新状态。
- 计算风险等级。
- 计算简单趋势指标。

一期可以继续使用现有脚本：

- `scripts/download_flood_water_levels.py`
- `scripts/import_water_levels_sqlite.py`
- `scripts/check_local_database.py`

后续可将脚本能力迁移到后端 `tasks/` 模块，由 APScheduler、Celery Beat 或系统 cron 调度。

### 3.3 数据存储层

一期可以继续使用 `data/local/shenzhen_water.db` 验证闭环。正式架构按 PostgreSQL + PostGIS 设计，以支持空间点位、行政区边界、空间查询和后续道路/降雨图层扩展。

原始 JSON 和 CSV 继续保留在 `download/` 目录，便于追溯数据来源。

### 3.4 服务层

后端 FastAPI 提供业务接口：

- 地图点位接口。
- 行政区边界接口。
- 全市态势统计接口。
- 行政区统计接口。
- 历史水位查询接口。
- 点位坐标候选生成接口。
- 坐标审核接口。
- 数据导入状态接口。

前端不直接访问数据库，也不直接调用采集脚本。

### 3.5 前端应用层

前端采用混合型结构：默认进入指挥地图首页，同时保留后台管理入口。

核心页面包括：

- 指挥地图首页。
- 历史查询页。
- 点位校核页。
- 数据状态页。

地图能力通过 `MapProvider` 封装。一期 Provider 使用高德地图，业务组件不直接依赖高德 SDK 对象，后续如需切换百度地图，可替换 Provider 实现。

## 4. 数据库设计

正式系统建议使用 PostgreSQL + PostGIS。一期 SQLite 可以按相同业务模型简化落地。

### 4.1 监测点主表 `monitor_points`

用途：统一管理积涝点和测站基础信息。

建议字段：

| 字段 | 含义 |
|---|---|
| `id` | 主键 |
| `station_code` | 测站编码 |
| `name` | 点位名称 |
| `point_type` | 点位类型 |
| `district_code` | 行政区编码 |
| `district_name` | 行政区名称 |
| `status` | 启用状态 |
| `created_at` | 创建时间 |
| `updated_at` | 更新时间 |

### 4.2 点位坐标表 `point_locations`

用途：支撑高德地理编码候选坐标和人工审核。

建议字段：

| 字段 | 含义 |
|---|---|
| `id` | 主键 |
| `point_id` | 监测点 ID |
| `longitude` | 经度 |
| `latitude` | 纬度 |
| `coord_system` | 坐标系，例如 GCJ-02 |
| `location_source` | 坐标来源，例如 amap_geocode、manual |
| `geocode_address` | 地理编码匹配地址 |
| `confidence` | 候选坐标置信度 |
| `review_status` | pending、approved、rejected |
| `reviewed_by` | 审核人 |
| `reviewed_at` | 审核时间 |
| `geom` | PostGIS 空间点 |

地图展示只使用 `review_status = approved` 的坐标。

### 4.3 水位观测明细表 `water_level_observations`

用途：存储历史水位明细。

建议字段：

| 字段 | 含义 |
|---|---|
| `id` | 主键 |
| `source_record_id` | 原始记录 ID |
| `station_code` | 测站编码 |
| `point_id` | 监测点 ID |
| `observed_at` | 观测时间 |
| `water_level_m` | 水位，单位米 |
| `raw_water_level` | 原始水位文本 |
| `source_file` | 来源文件 |
| `created_at` | 入库时间 |

建议索引：

- `(point_id, observed_at)`
- `(station_code, observed_at)`
- `observed_at`

### 4.4 点位最新状态表 `latest_point_status`

用途：支撑地图快速加载。

建议字段：

| 字段 | 含义 |
|---|---|
| `point_id` | 监测点 ID |
| `latest_observed_at` | 最新观测时间 |
| `water_level_m` | 最新水位 |
| `risk_level` | normal、attention、warning、danger、nodata |
| `trend` | rising、falling、stable、fluctuating、nodata |
| `data_status` | normal、delayed、missing |
| `updated_at` | 更新时间 |

### 4.5 风险阈值表 `risk_thresholds`

用途：一期支持统一风险规则，二期支持点位级阈值。

建议字段：

| 字段 | 含义 |
|---|---|
| `id` | 主键 |
| `point_id` | 监测点 ID，可为空表示全局规则 |
| `threshold_type` | global 或 point |
| `attention_level_m` | 关注阈值 |
| `warning_level_m` | 警戒阈值 |
| `danger_level_m` | 危险阈值 |
| `enabled` | 是否启用 |

### 4.6 行政区边界表 `admin_districts`

用途：展示深圳各区边界，并支持按区统计。

建议字段：

| 字段 | 含义 |
|---|---|
| `district_code` | 行政区编码 |
| `district_name` | 行政区名称 |
| `level` | 行政层级 |
| `geom` | PostGIS Polygon 或 MultiPolygon |
| `source` | 数据来源 |

### 4.7 数据源与导入批次

`data_sources` 记录开放数据接口配置：

- 数据源名称。
- 接口 URL。
- 更新频率。
- 是否启用。
- 备注。

`import_batches` 记录每次导入：

- 数据源。
- 开始时间。
- 结束时间。
- 数据范围。
- 拉取行数。
- 导入行数。
- 成功或失败状态。
- 错误信息。
- 原始文件路径。

### 4.8 二期空间与业务扩展表

二期需要在 PostGIS 中补齐降雨、道路、历史易涝点、告警、工单、用户审计和预测结果。以下表一期可以不落地，但顶层设计需要提前确认，避免后续接口和页面反复返工。

`rainfall_observations` 用于存储降雨观测：

| 字段 | 含义 |
|---|---|
| `id` | 主键 |
| `station_code` | 雨量站编码 |
| `station_name` | 雨量站名称 |
| `observed_at` | 观测时间 |
| `rainfall_mm` | 降雨量，单位毫米 |
| `duration_minutes` | 统计时长 |
| `geom` | PostGIS 空间点 |
| `source_file` | 来源文件 |

`road_segments` 用于道路图层展示：

| 字段 | 含义 |
|---|---|
| `id` | 主键 |
| `road_name` | 道路名称 |
| `district_name` | 所属行政区 |
| `road_level` | 道路等级 |
| `status` | 启用状态 |
| `geom` | PostGIS LineString 或 MultiLineString |
| `source` | 数据来源 |

`historical_flood_points` 用于历史易涝点图层：

| 字段 | 含义 |
|---|---|
| `id` | 主键 |
| `name` | 易涝点名称 |
| `district_name` | 所属行政区 |
| `risk_note` | 风险说明 |
| `source` | 数据来源 |
| `geom` | PostGIS 空间点或面 |

`alerts` 用于站内告警中心：

| 字段 | 含义 |
|---|---|
| `id` | 主键 |
| `point_id` | 关联监测点 |
| `alert_level` | 告警等级 |
| `alert_type` | 告警类型，例如 water_level、data_delay |
| `status` | active、acknowledged、closed |
| `triggered_at` | 触发时间 |
| `acknowledged_by` | 确认人 |
| `acknowledged_at` | 确认时间 |
| `closed_at` | 关闭时间 |

`work_orders` 用于处置工单：

| 字段 | 含义 |
|---|---|
| `id` | 主键 |
| `alert_id` | 关联告警 |
| `point_id` | 关联监测点 |
| `title` | 工单标题 |
| `status` | new、assigned、processing、completed、closed |
| `assignee_id` | 处理人 |
| `created_at` | 创建时间 |
| `completed_at` | 完成时间 |

`users`、`roles`、`user_roles` 用于基础权限：

| 字段 | 含义 |
|---|---|
| `users.id` | 用户主键 |
| `users.username` | 登录名 |
| `users.display_name` | 展示名 |
| `users.password_hash` | 密码哈希 |
| `users.enabled` | 是否启用 |
| `roles.id` | 角色主键 |
| `roles.code` | 角色编码 |
| `roles.name` | 角色名称 |
| `user_roles.user_id` | 用户 ID |
| `user_roles.role_id` | 角色 ID |

`audit_logs` 用于记录后台关键操作：

| 字段 | 含义 |
|---|---|
| `id` | 主键 |
| `user_id` | 操作人 |
| `action` | 操作类型 |
| `target_type` | 操作对象类型 |
| `target_id` | 操作对象 ID |
| `detail` | 操作详情 |
| `created_at` | 操作时间 |

`model_predictions` 用于规则型预测结果展示：

| 字段 | 含义 |
|---|---|
| `id` | 主键 |
| `point_id` | 监测点 ID |
| `predicted_for` | 预测目标时间 |
| `predicted_risk_level` | 预测风险等级 |
| `predicted_trend` | 预测趋势 |
| `confidence` | 置信度 |
| `model_version` | 规则或模型版本 |
| `created_at` | 生成时间 |

`sync_jobs` 和 `sync_job_runs` 用于后端调度：

| 字段 | 含义 |
|---|---|
| `sync_jobs.id` | 任务主键 |
| `sync_jobs.job_type` | 任务类型 |
| `sync_jobs.enabled` | 是否启用 |
| `sync_jobs.schedule` | 定时配置 |
| `sync_job_runs.id` | 执行记录主键 |
| `sync_job_runs.job_id` | 关联任务 |
| `sync_job_runs.status` | running、success、failed |
| `sync_job_runs.started_at` | 开始时间 |
| `sync_job_runs.finished_at` | 结束时间 |
| `sync_job_runs.error_message` | 失败原因 |

### 4.9 二期索引与数据口径

PostGIS 版本需要为 `geom` 字段建立空间索引，为 `observed_at`、`point_id`、`status`、`alert_level` 等常用过滤字段建立普通索引。业务口径保持和一期一致：

- `water_level_m IS NULL` 的记录进入原始层和历史明细，但不参与风险等级计算。
- 完全重复的 `source_record_id` 不重复进入业务统计。
- 地图点位只使用审核通过坐标。
- 降雨、道路、历史易涝点数据源不稳定时，允许使用可信样例数据先完成图层接口和前端开关。

## 5. 高德地图前后端设计

### 5.1 前端地图职责

高德 JS API 负责：

- 地图底图。
- 深圳范围定位。
- 点位 Marker。
- 行政区 Polygon。
- InfoWindow。
- 地理编码。
- 缩放、平移、聚合和交互。

业务组件不直接散落调用高德 SDK，而是通过 `MapProvider` 使用地图能力。

建议 Provider 方法：

- `initMap()`
- `fitToShenzhen()`
- `addRiskMarkers(points)`
- `drawDistrictPolygons(districts)`
- `openPointPopup(point)`
- `setRiskFilter(levels)`
- `geocodeAddress(address)`

### 5.2 后端接口

核心接口建议如下。

`GET /api/map/points`

返回已审核坐标的点位、最新水位、风险等级、趋势、更新时间。用于地图主页面。

`GET /api/map/districts`

返回深圳行政区边界 GeoJSON 或简化边界数据。

`GET /api/stats/overview`

返回全市统计：

- 点位总数。
- 正常数量。
- 关注数量。
- 警戒数量。
- 危险数量。
- 无数据数量。
- 最新更新时间。

`GET /api/stats/districts`

返回各行政区风险统计：

- 行政区名称。
- 点位数量。
- 各风险等级数量。
- 最高风险等级。

`GET /api/points/{id}/history`

返回单点历史水位曲线，支持开始时间和结束时间。

`POST /api/locations/geocode-candidates`

根据点位名称或地址调用高德地理编码，生成候选坐标。

`POST /api/locations/{id}/review`

审核候选坐标，通过后点位进入地图展示。

`GET /api/imports/latest`

返回最近导入批次和数据源状态。

### 5.3 二期后端接口

二期接口继续放在 `/api/` 下，保持前后端分离。接口先满足演示闭环，复杂筛选和导出能力后续增强。

`POST /api/sync-jobs/{id}/run`

手动触发数据同步任务，返回执行记录 ID、开始时间和当前状态。

`GET /api/sync-jobs/runs/latest`

返回最近一次同步任务状态、成功失败结果、行数统计和失败原因。

`GET /api/thresholds`

返回全局阈值和点位级阈值配置。

`PUT /api/thresholds/{id}`

更新阈值配置，并触发对应点位风险重算。

`GET /api/alerts`

返回告警列表，支持按状态、等级、行政区、点位和时间范围筛选。

`GET /api/alerts/{id}`

返回告警详情，包括触发点位、触发水位、阈值、趋势和关联工单。

`POST /api/alerts/{id}/acknowledge`

确认告警，记录确认人、确认时间和审计日志。

`GET /api/layers/rainfall`

返回降雨点位或网格图层数据，用于地图叠加展示。

`GET /api/layers/roads`

返回道路图层 GeoJSON 或简化线数据。

`GET /api/layers/historical-flood-points`

返回历史易涝点图层数据。

`GET /api/work-orders`

返回处置工单列表，支持按状态、处理人、告警和点位筛选。

`POST /api/work-orders`

从告警或点位创建工单。

`PATCH /api/work-orders/{id}/status`

推进工单状态，支持 new、assigned、processing、completed、closed。

`GET /api/predictions`

返回点位预测结果，支持按点位、行政区和预测时间筛选。

`POST /api/auth/login`

登录接口，返回基础会话或令牌，用于保护后台页面。

`GET /api/users`

返回用户列表，用于用户和角色基础管理。

`GET /api/roles`

返回角色列表，用于页面保护和后台权限展示。

`GET /api/audit-logs`

返回审计日志，支持按用户、操作类型和时间范围筛选。

### 5.4 地图展示规则

风险颜色：

- 正常：绿色。
- 关注：黄色。
- 警戒：橙色。
- 危险：红色。
- 无数据：灰色。

Marker 弹窗展示：

- 点位名称。
- 当前水位。
- 风险等级。
- 趋势。
- 观测时间。
- 所属行政区。
- 历史曲线入口。

二期弹窗可增加：

- 告警状态。
- 点位级阈值。
- 降雨摘要。
- 预测风险。
- 创建工单入口。

## 6. 前端页面功能

### 6.1 指挥地图首页

默认首页为指挥地图页。

主要区域：

- 顶部导航：系统名称、页面入口、数据更新时间。
- 左侧态势面板：全市统计、各区风险排行、图层开关。
- 中间高德地图：行政区边界、积涝点 Marker、点位聚合、点位筛选。
- 右侧风险列表：高风险点位、最新状态、详情入口。

主要交互：

- 按风险等级筛选。
- 按行政区筛选。
- 点位搜索。
- 点击 Marker 查看详情。
- 打开历史曲线。
- 地图自动聚焦深圳范围。

### 6.2 历史查询页

支持按点位、行政区、风险等级和时间范围查询历史水位。

一期功能：

- 单点水位曲线。
- 历史明细表。
- 时间范围筛选。

二期扩展：

- 多点对比。
- 导出报表。
- 与降雨数据叠加分析。

### 6.3 点位校核页

用于解决坐标缺口。

功能包括：

- 待审核点位列表。
- 高德地理编码候选坐标。
- 候选地址和置信度展示。
- 地图预览候选位置。
- 人工确认、驳回或手动修正经纬度。

审核通过后，点位进入正式地图展示。

### 6.4 数据状态页

用于展示数据链路运行情况。

功能包括：

- 数据源列表。
- 最近一次拉取时间。
- 拉取行数。
- 导入行数。
- 成功或失败状态。
- 错误信息。
- 原始文件路径。

### 6.5 二期后台页面

二期后台页面围绕防汛处置主链路展开，不追求复杂管理平台，优先保证告警、阈值、调度、工单和审计可演示。

告警中心：

- 告警列表。
- 告警等级、状态、行政区和时间筛选。
- 告警详情。
- 告警确认。
- 从告警创建工单。

阈值配置页：

- 全局阈值配置。
- 点位级阈值配置。
- 启用或停用点位级阈值。
- 保存后提示风险重算状态。

调度状态页：

- 同步任务列表。
- 最近运行状态。
- 手动触发同步。
- 失败原因查看。

审计日志页：

- 操作人筛选。
- 操作类型筛选。
- 操作对象和时间查看。

处置工单页：

- 工单列表。
- 创建、分派、处理中、完成、关闭状态流转。
- 关联告警和点位详情入口。

预测结果页：

- 未来风险等级列表。
- 预测趋势展示。
- 点位详情中的预测摘要。

扩展图层能力：

- 降雨图层开关和图例。
- 道路图层开关和图例。
- 历史易涝点图层开关和图例。
- 图层缺数据时显示空状态，不阻断核心积涝点地图。

## 7. 后端项目框架

建议目录结构：

```text
backend/
  app/
    main.py
    core/
      config.py
      database.py
      scheduler.py
    api/
      routes_map.py
      routes_points.py
      routes_stats.py
      routes_locations.py
      routes_imports.py
      routes_sync_jobs.py
      routes_thresholds.py
      routes_alerts.py
      routes_layers.py
      routes_work_orders.py
      routes_predictions.py
      routes_auth.py
      routes_users.py
      routes_audit_logs.py
    models/
      point.py
      water_level.py
      threshold.py
      district.py
      import_batch.py
      alert.py
      work_order.py
      user.py
      role.py
      audit_log.py
      prediction.py
      user.py
      layer.py
      sync_job.py
    schemas/
      point.py
      map.py
      stats.py
      location.py
      alert.py
      work_order.py
      prediction.py
      layer.py
      sync_job.py
    services/
      risk_service.py
      trend_service.py
      map_service.py
      geocode_service.py
      import_service.py
      alert_service.py
      threshold_service.py
      work_order_service.py
      prediction_service.py
      auth_service.py
      user_service.py
      audit_service.py
    repositories/
      point_repo.py
      water_level_repo.py
      district_repo.py
      alert_repo.py
      work_order_repo.py
    tasks/
      sync_open_data.py
  tests/
  pyproject.toml
```

职责划分：

- `api/` 只处理 HTTP 请求和响应。
- `services/` 放业务逻辑，例如风险等级、趋势计算、坐标审核。
- `repositories/` 封装数据库访问。
- `models/` 定义数据库模型。
- `schemas/` 定义 API 输入输出结构。
- `tasks/` 承接现有采集脚本能力。

## 8. 前端项目框架

建议目录结构：

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
      alerts.ts
      thresholds.ts
      layers.ts
      workOrders.ts
      predictions.ts
      syncJobs.ts
      auth.ts
      users.ts
      auditLogs.ts
    map/
      MapProvider.ts
      AMapProvider.ts
    views/
      CommandMap.vue
      HistoryQuery.vue
      LocationReview.vue
      DataStatus.vue
      AlertCenter.vue
      ThresholdSettings.vue
      SyncStatus.vue
      AuditLogs.vue
      WorkOrders.vue
      PredictionResults.vue
    components/
      RiskSummaryPanel.vue
      DistrictStatsPanel.vue
      HighRiskList.vue
      PointPopup.vue
      WaterLevelChart.vue
      LayerLegend.vue
      AlertDetailPanel.vue
      WorkOrderStatusStepper.vue
    stores/
      mapStore.ts
      statusStore.ts
      alertStore.ts
      layerStore.ts
```

前端设计重点：

- 地图业务组件通过 `MapProvider` 使用地图能力。
- API 调用集中在 `src/api/`。
- 指挥地图页面由面板组件和地图组件组合。
- 历史曲线组件可复用于弹窗和历史查询页。

## 9. 风险等级与趋势设计

一期使用统一风险规则，并预留点位级阈值。

建议等级：

- `normal`：正常。
- `attention`：关注。
- `warning`：警戒。
- `danger`：危险。
- `nodata`：无数据。

趋势指标：

- `rising`：持续上升。
- `falling`：持续下降。
- `stable`：基本稳定。
- `fluctuating`：波动。
- `nodata`：数据不足。

趋势可基于最近若干条观测值计算。一期只做解释性趋势，不做复杂预测。

二期风险计算优先使用点位级阈值；没有点位级阈值时回退到全局阈值。阈值更新后，应重算对应点位最新状态，并根据新风险结果生成或关闭告警。告警生成要保证幂等：同一告警条件已经存在 active 告警时，不重复生成新告警。

## 10. 主链路与异常降级

### 10.1 数据同步链路

```text
开放数据接口 -> 原始 JSON/CSV 归档 -> 导入数据库 -> 数据质量检查 -> 最新状态快照 -> 风险与趋势计算 -> 地图和统计 API
```

一期使用脚本手动运行或命令行触发。二期把脚本能力纳入 `sync_jobs`，支持手动触发、定时执行、状态记录和失败原因查看。

### 10.2 告警处置链路

```text
最新水位状态 -> 阈值匹配 -> 告警生成 -> 告警确认 -> 创建工单 -> 工单流转 -> 工单关闭
```

告警中心是二期最小可用闭环。真实短信、电话或第三方推送不作为本轮硬性目标，接口可以预留 `notification_status` 或扩展服务位置。

### 10.3 扩展图层链路

```text
降雨/道路/历史易涝点样例数据 -> PostGIS 图层表 -> 图层 API -> 地图开关和图例
```

扩展图层不阻塞一期核心地图。如果样例数据缺失，前端展示空状态，后端返回空集合和数据源状态。

### 10.4 预测展示链路

```text
历史水位 + 当前趋势 + 降雨摘要 -> 规则型预测结果 -> 预测 API -> 地图弹窗或预测页面
```

本轮预测以规则型结果展示为主，不要求训练复杂机器学习模型。预测结果必须带 `model_version` 和生成时间，避免被误解为实时权威预报。

### 10.5 异常与降级规则

- 开放数据接口失败：保留最近一次成功数据，数据状态页显示失败原因。
- 水位为空：进入历史明细，不参与风险计算，点位风险可显示 `nodata`。
- 点位无审核坐标：不进入正式地图，但保留在点位校核列表。
- 高德地理编码失败：记录失败原因，允许人工录入经纬度。
- PostGIS 未就绪：一期 SQLite 闭环继续可用，二期图层和空间查询暂不可用。
- 扩展图层缺数据：地图核心点位继续展示，图层面板显示暂无数据。
- 告警重复触发：已有 active 告警时更新告警最新触发信息，不重复创建。

## 11. 建设路线

### 11.1 一期验收成果

一期验收应包括：

1. 能拉取积涝点水位数据，保存原始 JSON 和汇总 CSV。
2. 能导入数据库，并记录导入批次。
3. 能生成高德地理编码候选坐标。
4. 能人工审核坐标，审核通过后进入地图。
5. 能按统一规则计算风险等级。
6. 能展示高德指挥地图、行政区边界、点位 Marker 和详情弹窗。
7. 能展示全市风险统计和各区风险统计。
8. 能查询单点历史水位曲线。
9. 能查看数据源导入状态。

### 11.2 二期扩展

二期扩展方向：

- SQLite 迁移到 PostgreSQL + PostGIS。
- 采集脚本升级为后端调度任务。
- 支持点位级风险阈值。
- 增加告警推送。
- 增加用户、角色、审计。
- 接入降雨数据。
- 接入道路和历史易涝点图层。
- 增加处置工单。
- 增加预测模型结果展示。

### 11.3 Day 2 完成确认清单

Day 2 顶层设计完成后，应确认：

- 系统架构已明确为 FastAPI + Vue + 高德 JS API。
- 一期 SQLite 闭环和二期 PostGIS 扩展边界清楚。
- 一期核心表、二期扩展表和关键索引口径已明确。
- 一期地图、统计、历史、校核、导入状态 API 已明确。
- 二期调度、阈值、告警、图层、工单、预测、审计 API 已明确。
- 指挥地图、历史查询、点位校核、数据状态页面已明确。
- 告警中心、阈值配置、调度状态、审计日志、工单、预测和扩展图层页面已明确。
- 数据同步、告警处置、扩展图层和预测展示主链路已明确。
- 无坐标、无水位、接口失败、PostGIS 未就绪和图层缺数据的降级规则已明确。
- Day 3 可以基于本设计规划 `backend/`、`frontend/`、`data/geo/` 和环境清单。

## 12. 当前项目适配建议

当前项目已有：

- `task.md`：原始需求说明。
- `docs/data_reference.md`：数据源和字段说明。
- `download/data_download_workflow.md`：数据下载流程。
- `scripts/download_flood_water_levels.py`：开放数据下载脚本。
- `scripts/import_water_levels_sqlite.py`：SQLite 导入脚本。
- `data/local/shenzhen_water.db`：本地 SQLite 数据库。
- `tests/`：部分脚本测试。

下一步建议不是马上重写项目，而是按本设计逐步补齐：

1. 先整理 SQLite 表结构，使其接近目标模型。
2. 新增点位坐标候选和审核数据结构。
3. 新增 FastAPI 地图接口。
4. 新增 Vue 指挥地图页。
5. 再把采集脚本纳入后端任务体系。
