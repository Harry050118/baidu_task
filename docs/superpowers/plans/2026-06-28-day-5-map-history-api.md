# Day 5 地图与历史 API 交付说明

> 日期：2026-06-28  
> 交付物：地图点位、点位详情、历史水位和数据时间范围 API

## 1. 今日结论

Day 5 在 Day 4 FastAPI 骨架和只读 SQLite Repository 基础上，完成了后端监测闭环的第一组主线查询接口。

核心结论：

- 新增 `/api` 路由结构，接口代码集中在 `backend/app/api/routes.py`。
- 地图点位接口只返回积涝点，数据来源固定为 `stations + flood_water_levels`。
- 当前数据库无经纬度字段，因此接口不输出 `longitude` 或 `latitude`，也不编造坐标。
- 所有地图点位明确返回 `has_coordinates=false` 和 `coordinate_status=missing_coordinates`。
- 水库水位不进入地图点位、点位详情或历史水位主线，仅在数据时间范围接口中作为质量摘要旁路出现。
- 点位详情和历史接口只接受积涝点测站编码；不存在或非积涝点统一返回 `404`。
- 历史接口支持 `limit`，默认 `500`，允许范围为 `1` 至 `5000`。
- 全量测试通过：`24 tests OK`。

## 2. 新增 API

### 2.1 `GET /api/map/points`

用途：为前端地图闭环提供积涝点列表和最新水位。

数据来源：

```text
stations
+ flood_water_levels
```

返回口径：

| 字段 | 说明 |
|---|---|
| `station_code` | 测站编码 |
| `station_name` | 测站名称 |
| `station_type` | 站类，当前均为 `内涝水情站` |
| `latest_observed_at` | 最新积涝水位观测时间 |
| `latest_water_level_m` | 最新数字水位，单位米 |
| `raw_water_level` | 原始水位文本 |
| `has_coordinates` | 当前固定为 `false` |
| `coordinate_status` | 当前固定为 `missing_coordinates` |

验收事实：

- 返回 `148` 个积涝点。
- 不包含水库测站。
- 不包含 `longitude` 或 `latitude`。

### 2.2 `GET /api/points/{station_code}`

用途：返回单个积涝点基础信息、最新水位和坐标状态。

返回内容：

- `station`：测站编码、名称、站类。
- `latest_water_level`：最新观测时间、最新水位、原始水位。
- `coordinates`：当前坐标缺失状态。

错误口径：

- `station_code` 不存在：`404`
- `station_code` 存在但不是积涝点：`404`
- 错误信息：`flood station not found`

### 2.3 `GET /api/points/{station_code}/history`

用途：返回单个积涝点历史水位序列。

查询参数：

| 参数 | 默认值 | 范围 | 说明 |
|---|---:|---:|---|
| `limit` | `500` | `1-5000` | 返回最近 N 条历史水位 |

排序口径：

```text
observed_at DESC, id DESC
```

数据来源：

```text
flood_water_levels
```

错误口径与点位详情接口一致：不存在或非积涝点统一返回 `404`。

### 2.4 `GET /api/data/time-range`

用途：返回主线数据时间范围，并保留水库数据质量摘要。

主线返回：

| 字段 | 值 |
|---|---|
| `flood_water_levels.observed_at_min` | `2025-12-31 23:50:23` |
| `flood_water_levels.observed_at_max` | `2026-06-23 00:47:39` |

水库旁路摘要：

- `quality_role=status_summary_only`
- `rows`
- `null_water_level_rows`

该接口中的水库信息只用于数据状态/质量展示，不进入地图点位或风险研判主线。

## 3. 代码变更

| 文件 | 作用 |
|---|---|
| `backend/app/api/__init__.py` | API 包初始化 |
| `backend/app/api/routes.py` | Day 5 API 路由 |
| `backend/app/main.py` | 挂载 `/api` 路由 |
| `backend/app/repositories/water_repository.py` | 增加积涝点校验和单点最新水位查询 |
| `tests/test_backend_day5.py` | Day 5 API 测试 |

## 4. 测试结果

已运行：

```bash
.venv/bin/python -m unittest tests/test_backend_day5.py
.venv/bin/python -m unittest tests/test_backend_day4.py
.venv/bin/python -m unittest discover tests
```

结果：

```text
24 tests OK
```

覆盖重点：

- 服务可启动，Day 4 `/health` 未回退。
- `/api/map/points` 返回 148 个积涝点。
- 地图点位不包含水库测站。
- 地图点位不包含编造坐标。
- 历史接口返回真实水位序列，并按时间倒序。
- 数据时间范围与 Day 3 事实一致。
- 非积涝点或不存在点位返回清晰错误。

## 5. 后续衔接

Day 5 只完成地图与历史查询的只读 API，不做以下工作：

- 不补坐标。
- 不调用高德 API。
- 不做坐标批量补全。
- 不做风险研判。
- 不做统计汇总扩展。
- 不把水库水位纳入地图点位。

后续 Day 6 可在当前接口基础上继续实现统计与状态 API，包括全市统计、导入批次、数据新鲜度和质量摘要。
