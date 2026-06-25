# Day 6 统计与状态 API 交付说明

> 日期：2026-06-29  
> 交付物：统计概览、数据状态和最近导入批次 API

## 1. 今日结论

Day 6 在 Day 5 地图与历史 API 基础上，补充了统计与数据状态接口，为后续前端数据状态页和地图统计面板做准备。

核心结论：

- 新增 3 个只读接口：`/api/stats/overview`、`/api/status/data`、`/api/imports/latest`。
- 统计主线仍只使用 `stations + flood_water_levels`。
- `/api/stats/overview` 不返回风险等级统计，Day 6 不做风险研判。
- `/api/status/data` 明确当前积涝点数据可用于点位查询，但因缺少经纬度，不能用于真实地图落点。
- `reservoir_water_levels` 只在数据状态接口中作为 `status_summary_only` 质量摘要出现，不进入地图点位和积水风险主线。
- `/api/imports/latest` 基于 `source_imports` 真实字段返回最近导入批次，不编造导入状态、错误信息或失败原因。
- 全量测试通过：`27 tests OK`。

## 2. 新增 API

### 2.1 `GET /api/stats/overview`

用途：为地图统计面板提供全市主线统计事实。

返回口径：

| 字段 | 值 |
|---|---:|
| `flood_station_count` | `148` |
| `latest_observed_at` | `2026-06-23 00:47:39` |
| `flood_record_count` | `4,101,063` |
| `stations_total` | `485` |
| `coordinate_status` | `missing_coordinates` |
| `has_coordinates` | `false` |

该接口不包含水库水位统计，也不包含风险等级统计。

### 2.2 `GET /api/status/data`

用途：为数据状态页提供数据范围、坐标状态、数据新鲜度和水库旁路质量摘要。

主线返回：

- `flood_water_levels.record_count=4101063`
- `flood_water_levels.unique_station_codes=148`
- `flood_water_levels.observed_at_min=2025-12-31 23:50:23`
- `flood_water_levels.observed_at_max=2026-06-23 00:47:39`
- `flood_water_levels.map_query_ready=true`
- `flood_water_levels.real_map_placement_ready=false`
- `stations.total=485`
- `stations.coordinate_status=missing_coordinates`
- `stations.has_coordinates=false`
- `stations.missing_coordinate_stations=485`

数据新鲜度：

- `data_freshness.latest_observed_at=2026-06-23 00:47:39`
- `data_freshness.status=historical_snapshot`

水库旁路摘要：

- `reservoir_water_levels.quality_role=status_summary_only`
- `reservoir_water_levels.record_count=2040352`
- `reservoir_water_levels.unique_station_codes=178`
- `reservoir_water_levels.null_water_level_rows=40982`
- `reservoir_water_levels.missing_station_codes=9`

### 2.3 `GET /api/imports/latest`

用途：返回 `source_imports` 中最近导入时间对应的真实导入记录。

当前最近导入批次：

| 字段 | 值 |
|---|---:|
| `latest_imported_at` | `2026-06-23T06:43:59+00:00` |
| `import_count` | `13` |
| `total_row_count` | `6,141,915` |

`items` 按 `id` 升序返回真实字段：

- `id`
- `source_file`
- `source_format`
- `imported_at`
- `row_count`

`source_imports` 当前没有导入状态、错误信息或失败原因字段，因此接口不输出这些字段。

## 3. 代码变更

| 文件 | 作用 |
|---|---|
| `backend/app/api/routes.py` | 新增 Day 6 API 路由 |
| `backend/app/repositories/water_repository.py` | 新增统计、数据状态和最近导入批次只读查询 |
| `tests/test_backend_day6.py` | 新增 Day 6 API 测试 |

## 4. 测试结果

已运行：

```bash
.venv/bin/python -m unittest tests/test_backend_day6.py
.venv/bin/python -m unittest discover tests
git diff --check
```

结果：

```text
tests/test_backend_day6.py: 3 tests OK
unittest discover tests: 27 tests OK
git diff --check: no output
```

覆盖重点：

- `/api/stats/overview` 返回 Day 3 和 Day 5 已确认主线事实。
- `/api/status/data` 明确坐标缺失，且 `real_map_placement_ready=false`。
- `/api/status/data` 返回 `data_freshness.status=historical_snapshot`，避免把本地库误解为实时在线监测。
- 水库水位只以 `status_summary_only` 质量摘要形式出现。
- `/api/imports/latest` 返回 `source_imports` 中的真实记录。
- 服务可启动，既有 Day 4 和 Day 5 接口未回退。

## 5. 后续衔接

Day 6 不做以下工作：

- 不补坐标。
- 不调用高德 API。
- 不做坐标批量补全。
- 不做风险研判。
- 不做模型预测。
- 不把水库水位纳入地图点位或积水风险主线。

后续 Day 7 可在当前坐标缺失状态基础上继续实现坐标候选与审核 API。
