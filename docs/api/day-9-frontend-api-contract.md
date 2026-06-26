# Day 9 前端联调 API 合同

> 日期：2026-07-02  
> 适用范围：Day 4 至 Day 8 已完成的 FastAPI 后端接口  
> 基础地址：本地联调默认使用后端服务地址，接口路径如下文所列

## 1. 联调总口径

- 当前 API 面向前端地图监测、点位详情、历史查询、数据状态、坐标校核和规则研判页面。
- 当前只做规则研判和趋势提示，不提供模型预测、降雨、机器学习或批量坐标能力。
- 地图和风险主线只使用 `stations + flood_water_levels`。
- `reservoir_water_levels` 只作为状态/质量摘要返回，不进入地图点位、点位详情、历史曲线、统计风险主线或规则研判。
- 高德 Web 服务 Key 只在后端环境变量 `AMAP_WEB_SERVICE_KEY` 中使用，任何 API 响应不得返回 Key、完整带 Key URL 或 `key=` 参数。
- 当前没有实现 `/api/map/districts`。前端如果需要行政区边界，应先使用静态占位或等待后续坐标/边界数据任务，不要按已可用接口联调。

## 2. 通用错误响应

| 状态码 | 场景 | 响应口径 |
|---:|---|---|
| `404` | 点位不存在、非积涝点、候选不存在 | `{"detail":"flood station not found"}`、`{"detail":"station not found"}` 或 `{"detail":"location candidate not found"}` |
| `422` | 查询参数或请求体校验失败 | FastAPI 默认校验结构，顶层包含 `detail` |
| `503` | 后端依赖不可用，例如数据库不可用或缺少高德 Key | `{"detail":"database unavailable"}` 或 `{"detail":"AMAP_WEB_SERVICE_KEY is not configured"}` |

前端错误展示建议：

- `404`：展示“点位不存在或暂不支持该点位”。
- `422`：展示“请求参数不合法”，并提示用户修正输入。
- `503`：展示“后端依赖暂不可用”，不要把后端 detail 当作敏感调试信息展开给普通用户。

## 3. 健康检查

### `GET /health`

用途：确认服务可启动、数据库可访问。

成功响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `status` | string | 固定为 `ok` |
| `database.status` | string | 固定为 `ok` |
| `database.path` | string | 当前 SQLite 路径 |
| `database.tables` | string[] | 当前可见表名 |

数据库不可用时返回 `503`，detail 固定为 `database unavailable`。

## 4. 地图与点位

### `GET /api/map/points`

用途：地图首页点位列表。

顶层响应：

```json
{
  "points": []
}
```

`points[]` 稳定字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `station_code` | string | 测站编码 |
| `station_name` | string | 测站名称 |
| `station_type` | string | 当前主线均为 `内涝水情站` |
| `latest_observed_at` | string | 最新积涝点水位时间 |
| `latest_water_level_m` | number | 最新水位，单位米 |
| `raw_water_level` | string | 原始水位文本 |
| `has_coordinates` | boolean | 是否已有可进入地图的审核坐标 |
| `coordinate_status` | string | `missing_coordinates` 或 `approved` |

仅当 `has_coordinates=true` 时返回：

| 字段 | 类型 | 说明 |
|---|---|---|
| `longitude` | number | 经度 |
| `latitude` | number | 纬度 |
| `coord_source` | string | 当前可为 `amap` |
| `coord_quality` | string | 审核通过后为 `verified` |
| `review_status` | string | 审核通过后为 `approved` |

注意：`pending` 和 `rejected` 坐标候选不会进入地图点位输出。

### `GET /api/points/{station_code}`

用途：点位详情。

顶层响应字段：

| 字段 | 说明 |
|---|---|
| `station` | 点位基础信息 |
| `latest_water_level` | 最新积涝水位 |
| `coordinates` | 当前坐标状态 |

不存在或非积涝点返回 `404`，detail 为 `flood station not found`。

### `GET /api/points/{station_code}/history?limit=500`

用途：单点历史水位曲线。

参数：

| 参数 | 默认值 | 范围 | 说明 |
|---|---:|---:|---|
| `limit` | `500` | `1-5000` | 返回最近 N 条，按 `observed_at DESC, id DESC` 排序 |

顶层响应字段：

| 字段 | 说明 |
|---|---|
| `station` | 点位基础信息 |
| `items` | 历史水位记录列表 |

`limit` 超出范围返回 `422`。

## 5. 数据范围、统计和导入状态

### `GET /api/data/time-range`

用途：展示主线水位数据时间范围。

顶层字段：

| 字段 | 说明 |
|---|---|
| `flood_water_levels` | 积涝点主线时间范围 |
| `reservoir_water_levels` | 水库质量摘要，`quality_role=status_summary_only` |

### `GET /api/stats/overview`

用途：地图统计面板主线事实。

字段：

| 字段 | 说明 |
|---|---|
| `flood_station_count` | 积涝点数量 |
| `latest_observed_at` | 最新积涝点观测时间 |
| `flood_record_count` | 积涝点水位记录数 |
| `stations_total` | 测站基础信息总数 |
| `coordinate_status` | 坐标总体状态 |
| `has_coordinates` | 原始测站表是否已有坐标字段 |

该接口不返回风险等级统计，不返回水库水位统计。

### `GET /api/stats/stations`

用途：站类分布统计。

字段：

| 字段 | 说明 |
|---|---|
| `total` | 测站总数 |
| `district_stats_available` | 当前固定为 `false` |
| `district_stats_reason` | 当前为 `missing_coordinates` |
| `items` | 站类和数量列表 |

### `GET /api/status/data`

用途：数据状态页。

顶层字段：

| 字段 | 说明 |
|---|---|
| `flood_water_levels` | 积涝点主线数据范围和可用性 |
| `stations` | 测站坐标缺口 |
| `reservoir_water_levels` | 水库状态摘要，`quality_role=status_summary_only` |
| `data_freshness` | 数据新鲜度，当前本地库为 `historical_snapshot` |

### `GET /api/imports/latest`

用途：最近导入批次。

字段：

| 字段 | 说明 |
|---|---|
| `latest_imported_at` | 最近导入时间 |
| `import_count` | 该时间批次记录数量 |
| `total_row_count` | 该批次总行数 |
| `items` | 导入记录列表 |

当前 `source_imports` 没有失败原因字段，前端不要依赖 `status` 或 `error` 字段。

## 6. 坐标候选与审核

### `GET /api/locations/status`

用途：坐标治理状态。

字段：

| 字段 | 说明 |
|---|---|
| `total_stations` | 测站总数 |
| `has_coordinate_columns` | 原始测站表是否已有坐标字段 |
| `coordinate_status` | 当前为 `missing_coordinates` |
| `candidate_count` | 候选坐标数量 |
| `approved_count` | 已审核通过数量 |
| `rejected_count` | 已拒绝数量 |
| `required_action` | 当前需要坐标来源和人工审核 |

### `POST /api/locations/geocode-candidates`

用途：为单个测站生成一个高德候选坐标。

请求体：

```json
{
  "station_code": "9281192008",
  "address": "深圳市南联第六工业区桥洞"
}
```

说明：

- 只支持单个对象，不支持数组。
- `address` 可选，缺省时后端使用 `深圳市 + station_name`。
- 缺少 `AMAP_WEB_SERVICE_KEY` 返回 `503`。
- 响应不包含 Key 或完整请求 URL。

### `GET /api/locations/{station_code}/candidates`

用途：查询单个测站候选坐标。

顶层字段：

| 字段 | 说明 |
|---|---|
| `station` | 测站基础信息 |
| `items` | 候选坐标列表 |

### `POST /api/locations/{station_code}/review`

用途：人工审核候选坐标。

请求体：

```json
{
  "candidate_id": 1,
  "review_status": "approved",
  "review_note": "人工核验可用"
}
```

`review_status` 只允许 `approved` 或 `rejected`。审核通过后候选坐标才可进入 `/api/map/points`。

## 7. 规则研判

### `GET /api/assessments`

用途：全市积涝点规则研判列表。

顶层响应：

```json
{
  "items": []
}
```

`items[]` 字段：

| 字段 | 说明 |
|---|---|
| `station_code` | 测站编码 |
| `station_name` | 测站名称 |
| `latest_observed_at` | 最新有效积涝水位时间 |
| `latest_water_level_m` | 最新有效积涝水位 |
| `risk_level` | `no_data`、`normal`、`attention`、`warning`、`danger` |
| `trend` | `no_data`、`stable`、`rising`、`falling`、`fluctuating` |
| `rule_version` | 当前为 `flood_rule_v1` |
| `rule_description` | 规则说明 |
| `generated_at` | 研判生成时间 |

### `GET /api/points/{station_code}/assessment`

用途：单个积涝点规则研判。

响应字段与 `items[]` 相同。不存在或非积涝点返回 `404`，detail 为 `flood station not found`。
