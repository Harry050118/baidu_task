# Day 7 坐标候选与审核 API 交付说明

> 日期：2026-06-30  
> 交付物：坐标候选、高德单点生成、人工审核和最小地图坐标闭环 API

## 1. 今日结论

Day 7 在 Day 5 地图与历史 API、Day 6 统计与状态 API 基础上，完成坐标候选与人工审核的最小后端闭环。

核心结论：

- 新增 `location_candidates` 空表，用于保存测站候选坐标、来源、质量和审核状态。
- 新增最小迁移脚本，只创建候选表和索引，不写入候选坐标，不做批量补全。
- 新增高德 Web 服务地理编码单点候选生成能力，只调用 `/v3/geocode/geo`。
- 不调用高德行政区域查询 `/v3/config/district`；该文档仅记录为后续行政区边界和区级统计依据。
- 高德 Key 只从后端 `AMAP_WEB_SERVICE_KEY` 读取，不写入日志，不返回 Key，不返回完整带 Key URL。
- 候选生成只允许单个 `station_code`，不支持批量请求。
- 高德候选默认标记为 `coord_source=amap`、`coord_quality=candidate`、`review_status=pending`。
- 人工审核通过后标记为 `coord_quality=verified`、`review_status=approved`。
- `/api/map/points` 只对最新 `approved` 候选输出经纬度；`pending` 和 `rejected` 候选不会进入地图点位输出。
- 高德坐标仍是临时审核坐标，不等同于政府标准坐标。

## 2. 官方文档依据

本日只使用高德开放平台官方 Web 服务文档：

- 地理/逆地理编码文档：`https://lbs.amap.com/api/webservice/guide/api/georegeo/`
- 行政区域查询文档：`https://lbs.amap.com/api/webservice/guide/api/district`

Day 7 实现范围只使用地理编码：

```text
GET https://restapi.amap.com/v3/geocode/geo
```

调用口径：

- `key`：后端 Web 服务 Key，必填。
- `address`：结构化地址，必填；默认使用 `深圳市 + station_name`。
- `city`：固定为 `深圳`。
- `output`：固定为 `JSON`。

行政区域查询后续可用于深圳行政区边界和区级统计，但 Day 7 不实现。

## 3. 新增数据表

新增表：

```text
location_candidates
```

核心字段：

| 字段 | 说明 |
|---|---|
| `station_code` | 测站编码，关联 `stations` |
| `longitude` | 经度 |
| `latitude` | 纬度 |
| `formatted_address` | 高德返回或请求使用的地址 |
| `amap_level` | 高德匹配级别 |
| `amap_adcode` | 高德行政区编码 |
| `coord_source` | 坐标来源，当前高德候选为 `amap` |
| `coord_quality` | 坐标质量，候选为 `candidate`，审核通过为 `verified` |
| `review_status` | 审核状态，支持 `pending`、`approved`、`rejected` |
| `reviewed_at` | 审核时间 |
| `review_note` | 审核备注 |
| `created_at` | 创建时间 |
| `updated_at` | 更新时间 |

迁移脚本：

```bash
.venv/bin/python scripts/migrate_location_candidates_sqlite.py
```

本脚本只创建表和索引，不批量补坐标。

## 4. 新增 API

### 4.1 `GET /api/locations/status`

用途：返回当前坐标治理状态。

返回口径：

- `total_stations`
- `has_coordinate_columns`
- `coordinate_status`
- `candidate_count`
- `approved_count`
- `rejected_count`
- `required_action`

当前 `stations` 原表仍没有经纬度、坐标来源、坐标质量和审核状态字段，因此 `coordinate_status` 仍为 `missing_coordinates`。

### 4.2 `POST /api/locations/geocode-candidates`

用途：为单个测站生成并保存高德候选坐标。

请求体：

```json
{
  "station_code": "9281192008",
  "address": "深圳市南联第六工业区桥洞"
}
```

说明：

- `station_code` 必填。
- `address` 可选，未传时使用 `深圳市 + station_name`。
- 只接受单个对象，不接受数组。
- 测站不存在返回 `404`。
- `AMAP_WEB_SERVICE_KEY` 缺失返回 `503`。
- 不返回 Key 或完整请求 URL。

### 4.3 `GET /api/locations/{station_code}/candidates`

用途：查询单个测站的候选坐标。

说明：

- 测站不存在返回 `404`。
- 无候选时返回空列表。
- 按 `created_at DESC, id DESC` 返回。

### 4.4 `POST /api/locations/{station_code}/review`

用途：人工审核候选坐标。

请求体：

```json
{
  "candidate_id": 1,
  "review_status": "approved",
  "review_note": "人工核验可用"
}
```

审核规则：

- `review_status=approved` 时写入 `coord_quality=verified`。
- `review_status=rejected` 时写入 `coord_quality=rejected`。
- 写入 `reviewed_at`、`updated_at` 和可选 `review_note`。

## 5. 地图点位输出规则

`/api/map/points` 继续只返回积涝点主线。

坐标输出规则：

- 无候选：不输出 `longitude` 或 `latitude`。
- `pending` 候选：不输出 `longitude` 或 `latitude`。
- `rejected` 候选：不输出 `longitude` 或 `latitude`。
- 最新 `approved` 候选：输出 `longitude`、`latitude`、`coord_source`、`coord_quality`、`review_status`。

该规则保证未审核候选不会成为正式地图点位。

## 6. 测试覆盖

新增测试文件：

```text
tests/test_backend_day7.py
```

覆盖重点：

- 迁移脚本创建空候选表。
- 坐标状态接口返回当前坐标缺口和候选统计。
- 不存在测站返回 `404`。
- 批量候选请求返回 `422`。
- Key 缺失返回 `503` 且不泄露 Key。
- 单点候选可保存并查询。
- 候选可审核通过或拒绝。
- `pending` 候选不进入 `/api/map/points`。
- `approved` 候选进入 `/api/map/points`。

Day 7 不做以下工作：

- 不批量补坐标。
- 不修改 `.env`。
- 不调用行政区域查询。
- 不做行政区统计。
- 不做风险研判。
- 不做模型训练。
- 不把高德坐标当作政府标准坐标。
