# Day 2 工程准备实施计划

> 更新基线：2026-06-24  
> 对应新排期：Day 2，2026-06-25  
> 目标：为监测闭环、坐标补全、规则研判和后期模型训练固定工程结构。

## 1. Day 2 目标

Day 2 不实现业务代码，只确认工程落点：

- `backend/` 后端工程结构。
- `frontend/` 前端工程结构。
- `data/` 数据目录结构。
- 高德 Key、SQLite、原始数据、模型产物的配置口径。
- 坐标补全和模型训练所需目录。

## 2. 推荐项目结构

```text
/Users/gjt/Documents/6.22/
  backend/
    app/
      main.py
      core/
      api/
      models/
      schemas/
      services/
        ingestion/
        quality/
        coordinates/
        assessment/
        prediction/
      repositories/
      tasks/
    tests/
    pyproject.toml
  frontend/
    src/
      main.ts
      router/
      api/
      map/
      views/
      components/
      stores/
  data/
    local/
    raw_samples/
    geo/
    features/
    models/
  docs/
    data_reference.md
    data_quality_report.md
    superpowers/
      specs/
      plans/
  download/
  scripts/
```

## 3. 后端目录职责

| 路径 | 职责 |
|---|---|
| `backend/app/core/` | 配置、数据库连接、通用响应 |
| `backend/app/api/` | 地图、历史、统计、坐标、研判、预测接口 |
| `backend/app/services/ingestion/` | 数据采集、导入、批次状态 |
| `backend/app/services/quality/` | 空值、重复、时间口径、数据新鲜度 |
| `backend/app/services/coordinates/` | 高德候选坐标、人工审核、政府标准坐标替换 |
| `backend/app/services/assessment/` | 初期规则研判和趋势提示 |
| `backend/app/services/prediction/` | 后期模型预测服务 |
| `backend/app/repositories/` | SQLite 查询封装，后续迁移 PostGIS |
| `backend/app/tasks/` | 定时采集、数据导入、样本生成、模型重训任务 |

## 4. 前端目录职责

| 路径 | 职责 |
|---|---|
| `frontend/src/views/CommandMap.vue` | 指挥地图首页 |
| `frontend/src/views/HistoryQuery.vue` | 历史水位查询 |
| `frontend/src/views/LocationReview.vue` | 坐标候选和审核 |
| `frontend/src/views/DataStatus.vue` | 数据导入状态 |
| `frontend/src/views/PredictionResults.vue` | 规则研判和后期模型预测展示 |
| `frontend/src/map/` | 高德地图 Provider、Marker、弹窗、边界 |
| `frontend/src/api/` | 后端接口封装 |

## 5. 数据目录职责

| 路径 | 职责 |
|---|---|
| `download/` | 原始开放数据 JSON、CSV、元数据 |
| `data/local/` | SQLite 数据库 |
| `data/geo/` | 行政区、道路、历史易涝点、政府标准坐标 |
| `data/features/` | 训练样本、特征表、样本切分记录 |
| `data/models/` | 模型文件、模型评估报告、版本说明 |

## 6. 配置项

后端配置：

```text
APP_ENV=local
DATABASE_URL=sqlite:///data/local/shenzhen_water.db
AMAP_WEB_SERVICE_KEY=
RAW_DATA_DIR=download
GEO_DATA_DIR=data/geo
FEATURE_DIR=data/features
MODEL_DIR=data/models
```

前端配置：

```text
VITE_API_BASE_URL=http://localhost:8000
```

配置规则：

- 真实高德 Key 不进入 Git。
- `.env.example` 只放变量名和空值。
- 项目只保留后端 `AMAP_WEB_SERVICE_KEY`，不再保留或使用前端 JS API Key。
- 前端如需高德相关能力，通过后端接口或后端代理间接调用。
- 坐标数据必须保留来源字段。
- 模型产物可以本地生成，后续再决定是否纳入版本管理。

## 7. SQLite 与下载数据确认

本地数据库路径固定为：

```text
data/local/shenzhen_water.db
```

当前文件大小约 1.7G。使用 `scripts/check_local_database.py` 和 SQLite schema 检查后，确认当前数据库包含以下业务表：

| 表 | 职责 | 当前数据量 |
|---|---|---:|
| `stations` | 测站基础信息 | 485 行 |
| `flood_water_levels` | 积涝点水位数据 | 4,101,063 行 |
| `reservoir_water_levels` | 水库水位数据 | 2,040,352 行 |
| `source_imports` | CSV 导入来源记录 | 13 行 |

当前主数据表合计 6,141,900 行，不含 `source_imports` 和 SQLite 内部表。

字段结构确认：

| 表 | 关键字段 |
|---|---|
| `stations` | `station_code`、`station_name`、`station_type`、`source_file`、`imported_at` |
| `flood_water_levels` | `id`、`station_code`、`observed_at`、`water_level_m`、`raw_water_level`、`source_file`、`imported_at` |
| `reservoir_water_levels` | `id`、`station_code`、`observed_at`、`water_level_m`、`raw_water_level`、`source_file`、`imported_at` |
| `source_imports` | `id`、`source_file`、`source_format`、`imported_at`、`row_count` |

数据范围确认：

- 积涝点水位数据：148 个测站编码，时间范围 `2025-12-31 23:50:23` 至 `2026-06-23 00:47:39`，全部 148 个测站编码均可在 `stations` 表匹配。
- 水库水位数据：178 个测站编码，时间范围 `2025-12-31 23:27:04` 至 `2026-06-23 00:35:00`，169 个测站编码可在 `stations` 表匹配，9 个暂未匹配。
- 测站基础信息表当前没有经纬度字段，因此坐标补全仍需走高德候选坐标、人工审核和政府标准坐标替换流程。

下载目录和 CSV 命名规则确认：

| 数据集 | 目录规则 | CSV 命名规则 |
|---|---|---|
| 测站基本信息表 | `download/市水务局测站基本信息表/` | `市水务局测站基本信息表_1392394662.csv` |
| 积涝点水位数据 | `download/市水务局积涝水位数据/YYYY-MM/` | `市水务局积涝点水位数据_2920001403147_YYYYMM.csv` |
| 水库水位表 | `download/市水务局水库水位表/YYYY-MM/` | `市水务局水库水位表_1952552493_YYYYMM.csv` |

当前 `download/` 中确认有 13 个 CSV 和 13 个 `download_metadata.json`。积涝点水位数据和水库水位表均已按 `2026-01` 至 `2026-06` 月份目录归档；测站基本信息表为单文件目录，并保留 `raw_pages/` 原始分页数据。

## 8. Day 3 前置清单

Day 3 开始数据源与坐标策略复核前，应确认：

- 高德 API Key：已准备，真实后端 Web 服务 Key 放在 `.env`，项目不再保留前端 JS API Key。
- 政府标准坐标申请材料：已由项目负责人提交申请。
- SQLite 当前表结构和数据量：已确认，详见本计划第 7 节。
- 下载目录和 CSV 命名规则：已确认，详见本计划第 7 节。
- 坐标字段设计：已确认采用 `coord_source`、`coord_quality`、`review_status`。
