# Day 6 统计与状态 API 设计

> 日期：2026-06-29  
> 交付物：统计与数据状态 API 设计

## 1. 背景

Day 5 已完成第一组 FastAPI 监测闭环接口：

- `GET /health`
- `GET /api/map/points`
- `GET /api/points/{station_code}`
- `GET /api/points/{station_code}/history`
- `GET /api/data/time-range`

Day 6 目标是在 Day 5 只读查询基础上，补充统计与数据状态 API，为后续前端数据状态页和地图统计面板做准备。

当前 SQLite 主线库仍为：

```text
data/local/shenzhen_water.db
```

主线业务表为：

- `stations`
- `flood_water_levels`

`reservoir_water_levels` 只作为数据状态和质量摘要旁路，不进入地图点位、积水风险主线统计或后续风险研判。

## 2. API 范围

Day 6 实现 3 个接口：

- `GET /api/stats/overview`
- `GET /api/status/data`
- `GET /api/imports/latest`

本轮暂不实现 `GET /api/stats/stations`。如果后续前端马上需要站类分布面板，再单独补充该接口。

## 3. 接口设计

### 3.1 `GET /api/stats/overview`

用途：为地图统计面板提供全市主线统计事实，不做风险研判。

数据来源：

```text
stations
+ flood_water_levels
```

返回字段：

| 字段 | 值 |
|---|---:|
| `flood_station_count` | `148` |
| `latest_observed_at` | `2026-06-23 00:47:39` |
| `flood_record_count` | `4,101,063` |
| `stations_total` | `485` |
| `coordinate_status` | `missing_coordinates` |
| `has_coordinates` | `false` |

该接口不返回风险等级统计。风险等级、趋势提示和规则说明属于后续规则研判工作。

### 3.2 `GET /api/status/data`

用途：为数据状态页提供数据范围、坐标状态和质量摘要。

返回结构包含：

- `flood_water_levels`
- `stations`
- `reservoir_water_levels`
- `data_freshness`

`flood_water_levels` 返回：

| 字段 | 说明 |
|---|---|
| `record_count` | 积涝点水位唯一记录数 |
| `unique_station_codes` | 积涝点唯一测站编码数 |
| `observed_at_min` | 积涝点最早观测时间 |
| `observed_at_max` | 积涝点最新观测时间 |
| `map_query_ready` | 是否可用于地图点位查询，当前为 `true` |
| `real_map_placement_ready` | 是否可用于真实地图落点，当前为 `false` |

`stations` 返回：

| 字段 | 说明 |
|---|---|
| `total` | 测站基础信息总数 |
| `coordinate_status` | 当前为 `missing_coordinates` |
| `has_coordinates` | 当前为 `false` |
| `missing_coordinate_stations` | 缺少坐标的测站数，当前为 `485` |

`reservoir_water_levels` 只返回旁路质量摘要：

| 字段 | 说明 |
|---|---|
| `quality_role` | 固定为 `status_summary_only` |
| `record_count` | 水库水位记录数 |
| `unique_station_codes` | 水库唯一测站编码数 |
| `null_water_level_rows` | 水库空水位记录数 |
| `missing_station_codes` | 水库未匹配测站基础信息的编码数 |

`data_freshness` 返回：

| 字段 | 说明 |
|---|---|
| `latest_observed_at` | 当前本地库积涝点最新观测时间 |
| `status` | 当前为 `historical_snapshot` |
| `message` | 说明当前本地库可用于 API 验证，不代表实时在线监测 |

该接口需要明确表达：当前积涝点数据可以支撑点位查询，但由于 `stations` 没有经纬度，不能支撑准确真实地图落点；同时当前本地库是历史快照，不应被误解为实时在线监测数据。

### 3.3 `GET /api/imports/latest`

用途：基于 `source_imports` 返回最近导入批次摘要。

已确认 `source_imports` 表结构：

| 字段 | 类型 |
|---|---|
| `id` | `INTEGER PRIMARY KEY AUTOINCREMENT` |
| `source_file` | `TEXT NOT NULL` |
| `source_format` | `TEXT NOT NULL` |
| `imported_at` | `TEXT NOT NULL` |
| `row_count` | `INTEGER NOT NULL` |

当前数据库有 13 条导入记录，`imported_at` 均为：

```text
2026-06-23T06:43:59+00:00
```

由于该表没有状态、错误信息或失败原因字段，Day 6 接口不编造导入成功、失败或错误详情。

返回字段：

| 字段 | 说明 |
|---|---|
| `latest_imported_at` | 最近导入时间 |
| `import_count` | 最近导入时间下的记录数 |
| `total_row_count` | 最近导入时间下的 `row_count` 合计 |
| `items` | 最近导入时间下的真实导入记录 |

`items` 按 `id` 升序返回真实字段：

- `id`
- `source_file`
- `source_format`
- `imported_at`
- `row_count`

## 4. 实现边界

Day 6 会做：

- 继续把 API 路由放在 `backend/app/api/routes.py`。
- 在 `backend/app/repositories/water_repository.py` 增加只读查询方法。
- 继续通过 `connect_readonly` 访问 SQLite。
- 尽量复用现有坐标状态查询口径。
- 新增 `tests/test_backend_day6.py`。

Day 6 不做：

- 不修改 `.env`。
- 不打印或暴露 `APP_KEY`、`AMAP_WEB_SERVICE_KEY`。
- 不重跑全量下载或导入归档。
- 不批量补坐标。
- 不编造坐标。
- 不做风险研判。
- 不做模型预测。
- 不把水库水位纳入积水风险主线。
- 不保留无关的 `docs/data_quality_report.md` 刷新差异。
- 不把未跟踪 Day 4 文档纳入 Day 6 工作。

## 5. 测试设计

新增 Day 6 测试，覆盖：

- FastAPI 服务仍可启动，`/health` 未回退。
- `/api/stats/overview` 返回 Day 3 和 Day 5 已确认事实。
- `/api/status/data` 明确坐标缺失，且 `real_map_placement_ready=false`。
- `/api/status/data` 返回 `data_freshness.status=historical_snapshot`。
- `reservoir_water_levels` 只以 `status_summary_only` 质量摘要形式出现。
- `/api/imports/latest` 返回 `source_imports` 中的真实记录。
- 最近导入批次记录数为 `13`，行数合计为真实数据库结果。
- 全量 `unittest` 通过。

## 6. 验收标准

Day 6 完成标准：

- 3 个接口返回稳定 JSON，字段与本设计一致。
- 所有数据库访问均为只读查询。
- Day 6 测试和既有全量测试通过。
- 工作树不包含无关 Day 4 文档或数据质量报告刷新差异。
