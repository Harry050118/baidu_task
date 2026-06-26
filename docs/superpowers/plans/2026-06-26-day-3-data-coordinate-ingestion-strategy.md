# Day 3 数据源、坐标与采集归档策略说明

> 日期：2026-06-26  
> 交付物：数据源与采集归档策略说明

## 1. 今日结论

Day 3 是数据底座封口工作包，覆盖当前 SQLite 数据库、测站字段、坐标缺口、高德 Web 服务 API 配置口径、开放数据采集归档、临时坐标补全流程和后续模型评估口径复核，为 Day 4 后端工程落地做准备。

核心结论：

- 当前 SQLite 主线库为 `data/local/shenzhen_water.db`。
- 本轮已只读复核 SQLite 三张核心表：`stations`、`flood_water_levels`、`reservoir_water_levels`。结构、数据量和时间范围与现有质量报告一致。
- `stations` 表只有测站编码、名称、站类和导入元数据，没有经纬度、坐标系、坐标来源、坐标质量或审核状态字段。
- 积涝点水位数据可以完整匹配测站基础信息；水库水位仍有 9 个测站编码无法匹配基础信息。
- 当前不能编造测站坐标。地图落点、空间分析和模型空间特征必须使用有来源、有质量状态、可审核的坐标。
- 高德配置口径收敛为后端 Web 服务 Key：真实 Key 只放 `.env`，不再保留或使用前端 JS API Key。
- 高德 Web 服务 API 已做最小可用性复测：HTTP `200`，高德 `status=1`，`info=OK`，`infocode=10000`，返回 1 条测试地理编码结果；测试未打印 Key 或完整 URL。
- 高德坐标只能作为候选坐标，必须经过人工审核；政府标准坐标是最终可信来源。
- leader 最新要求已纳入：后续模型需要在积涝水位数据基础上增加降水量维度；当前降水量尚未获取，先记录为待接入数据源。
- 当前开放数据下载脚本已支持测站基础信息、积涝点水位数据和水库水位表。本轮只读复核确认 CSV、原始分页 JSON 和下载元数据归档完整。

## 2. SQLite 数据库复核

数据库路径：

```text
data/local/shenzhen_water.db
```

检查命令：

```bash
python3 scripts/check_local_database.py
```

本轮复核未重跑导入脚本，使用 `sqlite3` 只读查询表结构、数据量、时间范围、空水位和测站匹配情况。

### 2.1 `stations`

表结构：

| 字段 | 类型 | 说明 |
|---|---|---|
| `station_code` | `TEXT PRIMARY KEY` | 测站编码 |
| `station_name` | `TEXT NOT NULL` | 测站名称 |
| `station_type` | `TEXT NOT NULL` | 站类 |
| `source_file` | `TEXT NOT NULL` | 来源 CSV |
| `imported_at` | `TEXT NOT NULL` | 导入时间 |

当前数据：

| 指标 | 值 |
|---|---:|
| 行数 | 485 |
| 唯一测站编码 | 485 |
| 导入时间 | `2026-06-23T06:43:59+00:00` |

当前未包含：

- 经度
- 纬度
- 坐标系
- 坐标来源
- 坐标质量
- 审核状态

### 2.2 `flood_water_levels`

表结构：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `TEXT PRIMARY KEY` | 原始水位记录 ID |
| `station_code` | `TEXT NOT NULL` | 测站编码 |
| `observed_at` | `TEXT NOT NULL` | 观测时间 |
| `water_level_m` | `REAL NOT NULL` | 数字水位，单位米 |
| `raw_water_level` | `TEXT NOT NULL` | 原始水位文本 |
| `source_file` | `TEXT NOT NULL` | 来源 CSV |
| `imported_at` | `TEXT NOT NULL` | 导入时间 |

索引：

- `idx_flood_water_levels_station_time (station_code, observed_at)`
- `idx_flood_water_levels_observed_at (observed_at)`

当前数据：

| 指标 | 值 |
|---|---:|
| 行数 | 4,101,063 |
| 唯一测站编码 | 148 |
| 时间范围 | `2025-12-31 23:50:23` 至 `2026-06-23 00:47:39` |
| 空水位记录 | 0 |
| 匹配测站基础信息 | 148 |
| 缺失测站基础信息 | 0 |

### 2.3 `reservoir_water_levels`

表结构：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `TEXT PRIMARY KEY` | 原始记录 ID |
| `station_code` | `TEXT NOT NULL` | 测站编码 |
| `observed_at` | `TEXT NOT NULL` | 采集时间 |
| `water_level_m` | `REAL` | 数字水位，单位米；允许为空 |
| `raw_water_level` | `TEXT NOT NULL` | 原始水位文本 |
| `source_file` | `TEXT NOT NULL` | 来源 CSV |
| `imported_at` | `TEXT NOT NULL` | 导入时间 |

索引：

- `idx_reservoir_water_levels_station_time (station_code, observed_at)`
- `idx_reservoir_water_levels_observed_at (observed_at)`

当前数据：

| 指标 | 值 |
|---|---:|
| 行数 | 2,040,352 |
| 唯一测站编码 | 178 |
| 时间范围 | `2025-12-31 23:27:04` 至 `2026-06-23 00:35:00` |
| 空水位记录 | 40,982 |
| 匹配测站基础信息 | 169 |
| 缺失测站基础信息 | 9 |

## 3. 经纬度缺口与约束

当前测站基础信息表没有经纬度字段，也没有坐标系字段；同时没有 `coord_source`、`coord_quality`、`review_status` 等坐标治理字段。因此当前数据库不能直接支持准确地图落点。

不能编造坐标，原因如下：

- 防汛和积水监测属于风险研判场景，错误坐标会把风险点展示到错误位置，影响调度判断。
- 编造坐标会污染后续人工审核、政府标准坐标替换和训练样本。
- 空间特征、行政区归属、道路匹配、站点邻近关系都依赖可信坐标，错误坐标会造成模型训练和评估偏差。
- 后续需要保留坐标来源、质量和审核状态，保证每个点位可追溯、可替换、可复核。

因此当前策略是：无可信坐标时不做正式地图落点；高德候选坐标只能作为候选或临时坐标，必须人工审核后才能进入正式展示或训练流程。政府或水务部门返回的标准坐标是最终可信来源，到位后应替换高德候选坐标并保留替换记录。

## 4. 坐标字段设计

后续坐标补全表或测站坐标扩展表固定保留以下字段：

| 字段 | 含义 | 示例 |
|---|---|---|
| `coord_source` | 坐标来源 | `amap`、`manual`、`government` |
| `coord_quality` | 坐标质量或精度状态 | `candidate`、`provisional`、`verified`、`official`、`rejected` |
| `review_status` | 人工审核状态 | `pending`、`approved`、`rejected`、`replaced` |

来源口径：

| `coord_source` | 说明 | 使用约束 |
|---|---|---|
| `amap` | 高德 Web 服务 API 生成的候选坐标 | 只能作为候选或临时坐标，必须人工审核，不能等同于政府标准坐标 |
| `manual` | 人工根据可信材料修正或确认的坐标 | 需要保留审核人、审核时间和依据，质量状态可为 `verified` |
| `government` | 政府或水务部门返回的标准坐标 | 最终可信来源，质量状态可为 `official`，到位后替换高德临时坐标 |

建议状态流转：

```text
amap candidate + pending
  -> manual verified + approved
  -> government official + replaced
```

如果高德候选结果明显错误：

```text
amap candidate + pending
  -> amap rejected + rejected
```

## 5. 高德 API 配置口径

项目只保留后端 Web 服务 Key：

```text
AMAP_WEB_SERVICE_KEY=
```

配置规则：

- 真实 Key 只放 `.env`。
- `.env.example` 只保留变量名和空值。
- 不在 Git、文档、日志、测试输出中打印真实 Key。
- 不再保留或使用前端 JS API Key。
- 前端如需高德能力，必须通过后端接口或后端代理间接使用高德 Web 服务能力。

最小可用性复测结果：

| 项目 | 结果 |
|---|---|
| Key 是否存在 | 是 |
| HTTP 状态码 | `200` |
| 高德 `status` | `1` |
| 高德 `info` | `OK` |
| 高德 `infocode` | `10000` |
| 测试返回数量 | `1` |

检测说明：

- 测试从 `.env` 读取 `AMAP_WEB_SERVICE_KEY`。
- 测试使用高德 Web 服务地理编码能力，从地点文本获取候选经纬度；这不是逆地理编码。
- 测试输出只保留 HTTP 状态码、`status`、`info`、`infocode`、`count`。
- 测试请求未打印 Key，也未记录完整请求 URL。
- 当前结果只证明 Web 服务 Key 可以完成一次低成本地理编码请求，不代表批量坐标补全质量已经通过。

## 6. 高德临时坐标补全策略

临时补全流程：

1. 从 `stations` 读取 `station_code`、`station_name`、`station_type`。
2. 优先用测站名称生成候选地址，例如 `深圳市 + station_name`。
3. 如果后续获得地址字段，再以地址作为优先候选输入。
4. 测站编码仅作为关联键和审计字段，不应单独作为地理编码地址。
5. 调用高德 Web 服务 API 生成候选坐标。
6. 写入候选坐标表，标记 `coord_source=amap`、`coord_quality=candidate`、`review_status=pending`。
7. 人工审核候选坐标，确认位置合理后改为 `coord_quality=verified`、`review_status=approved`。
8. 政府标准坐标返回后，以 `coord_source=government`、`coord_quality=official` 替换或覆盖临时坐标，并保留替换记录。

使用约束：

- 高德候选坐标不能直接当作政府标准坐标。
- 未审核候选坐标不能作为正式地图展示点位。
- 高德候选坐标进入训练样本时，必须保留来源和质量字段，方便后续政府坐标到位后重算样本。

## 7. 采集归档固化口径

当前下载脚本：

```text
scripts/download_flood_water_levels.py
```

已支持的数据集：

| 参数 | 数据源 | 是否按时间查询 | 输出目录 |
|---|---|---|---|
| `--dataset station` | 市水务局测站基本信息表 | 否 | `download/市水务局测站基本信息表/` |
| `--dataset flood` | 市水务局积涝点水位数据 | 是 | `download/市水务局积涝水位数据/YYYY-MM/` |
| `--dataset reservoir` | 市水务局水库水位表 | 是 | `download/市水务局水库水位表/YYYY-MM/` |

每次下载必须同时保留：

- 汇总 CSV。
- `raw_pages/page_*.json` 原始分页响应。
- `download_metadata.json` 下载元数据。

当前归档状态：

| 项目 | 值 |
|---|---:|
| `download_metadata.json` 文件数 | 13 |
| 原始分页 JSON 文件数 | 622 |
| 测站基础信息 CSV | 1 个 |
| 积涝点水位月度 CSV | 6 个 |
| 水库水位月度 CSV | 6 个 |
| CSV 行数与 metadata 一致性 | 全部一致 |
| `rows_downloaded` 与 `total_reported_by_api` 一致性 | 全部一致 |

本轮归档复核结果：

| 数据集 | 目录数量 | CSV 数量 | metadata 数量 | raw_pages 数量 | 行数一致性 |
|---|---:|---:|---:|---:|---|
| 测站基础信息 | 1 | 1 | 1 | 1 | 通过 |
| 积涝点水位 | 6 | 6 | 6 | 414 | 通过 |
| 水库水位 | 6 | 6 | 6 | 207 | 通过 |
| 合计 | 13 | 13 | 13 | 622 | 通过 |

目录和命名规则：

| 数据集 | 目录规则 | CSV 命名规则 |
|---|---|---|
| 测站基本信息表 | `download/市水务局测站基本信息表/` | `市水务局测站基本信息表_1392394662.csv` |
| 积涝点水位数据 | `download/市水务局积涝水位数据/YYYY-MM/` | `市水务局积涝点水位数据_2920001403147_YYYYMM.csv` |
| 水库水位表 | `download/市水务局水库水位表/YYYY-MM/` | `市水务局水库水位表_1952552493_YYYYMM.csv` |

下载完成后检查：

1. CSV 文件存在，且行数大于 1。
2. `download_metadata.json` 存在。
3. `rows_downloaded` 与 `total_reported_by_api` 一致。
4. `raw_pages/` 下存在分页 JSON。
5. 月度数据目录与 CSV 文件月份一致。
6. 不在日志、文档或提交中记录真实 `APP_KEY`。
7. 不在日志、文档或提交中记录真实 `AMAP_WEB_SERVICE_KEY`。

重跑口径：

- 重复运行同一输出目录会覆盖该目录中的 CSV、`download_metadata.json` 和 `raw_pages/page_*.json`。
- 全量重跑前应确认是否需要保留旧归档；如需保留，应复制到带日期的备份目录。
- 只做连通性验证时，使用 `--max-pages 1` 并输出到临时目录，避免覆盖正式归档。

失败记录口径：

- API 返回 `errorCode` 时，本次下载视为失败，错误码和错误信息应进入运行日志。
- HTTP 或网络错误时，本次下载视为失败，不应把半成品当作完整归档。
- 如果后续加入断点续传或重试机制，需要在 metadata 中记录失败页、重试次数和最终状态。
- Day 5 入库前，只使用 metadata 与 CSV 行数一致的归档作为输入。

## 8. 降水量待接入要求

leader 最新要求：后续模型需要在积涝水位数据基础上增加降水量维度。

当前状态：

- 积涝水位数据已经入库。
- 降水量数据尚未获取。
- 降水量先记录为待接入数据源。

后续降水量字段建议：

| 字段 | 说明 |
|---|---|
| `rainfall_mm` | 当前小时或当前观测窗口降水量 |
| `rainfall_1h_mm` | 近 1 小时累计降水量 |
| `rainfall_3h_mm` | 近 3 小时累计降水量 |
| `rainfall_24h_mm` | 近 24 小时累计降水量 |
| `rainfall_level` | 小雨、中雨、大雨、暴雨等雨强等级 |
| `rainfall_source` | 降水数据来源 |
| `rainfall_observed_at` | 降水观测时间 |

接入口径：

- 降水数据到位前，可以保留无降水基线模型或规则研判。
- 降水数据到位后，必须构建加入降水特征的增强样本。
- 降水站点、行政区或网格与积涝测站的匹配关系必须可追溯。

## 9. 实时分析和训练目标口径

当前下载目录 `download/市水务局积涝水位数据/` 提供的是积涝点水位观测数据，不是直接的积涝体积或积涝量。因此后续训练和实时分析不应写成“直接训练积涝量”，而应以近实时水位序列为基础，派生水位增长量、增长速度和风险状态。

分析粒度：

- 不以“一天”为主要分析粒度。日级统计只能用于汇总、报表和回看，不能满足实时防汛研判。
- 主线分析应尽量使用原始观测时间戳，按秒级时间差计算相邻观测之间的变化。
- 如果不同测站上报间隔不一致，应按实际 `observed_at` 计算时间差，而不是假设固定采样频率。

建议派生特征：

| 字段 | 说明 |
|---|---|
| `water_level_m` | 当前观测水位 |
| `delta_water_level_m` | 当前观测与上一条有效观测的水位差 |
| `delta_seconds` | 两条有效观测之间的秒级时间差 |
| `water_level_rate_mps` | `delta_water_level_m / delta_seconds`，表示每秒水位变化 |
| `water_level_rate_mpm` | 每分钟水位变化，便于业务展示 |
| `recent_max_water_level_m` | 最近窗口内最高水位 |
| `recent_rise_duration_seconds` | 最近连续上升持续时间 |
| `rainfall_mm` | 同一时间窗口内降水量，待接入 |
| `rainfall_intensity` | 降水强度或雨强等级，待接入 |

实时分析目标：

- 当前水位是否超过风险阈值。
- 水位是否快速上升。
- 当前降水是否正在强化积水风险。
- 在未来短时窗口内，点位是否可能进入更高风险等级。

训练目标建议：

- 基线阶段：仅使用积涝水位序列，预测短时水位变化、上升趋势或风险等级。
- 增强阶段：接入降水量后，使用“积涝水位序列 + 降水量”预测短时风险等级。
- 训练样本必须按观测时间构建，不能把一天内的全部未来数据聚合后再回填给早期时刻，否则会造成时间泄漏。

## 10. 训练和测试策略

后续模型采用时间序列切分，不允许随机切分。

6 月滚动测试口径：

- 以 6 月内每个预测日作为切分点。
- 预测日之前的数据作为训练集。
- 预测日及之后的数据作为测试集。
- 不得使用预测日及之后的数据训练模型。
- 所有特征工程必须遵守同一时间边界，避免时间泄漏。

示例：

| 预测日 | 训练集 | 测试集 |
|---|---|---|
| 2026-06-01 | `2026-06-01` 之前 | `2026-06-01` 及之后 |
| 2026-06-02 | `2026-06-02` 之前 | `2026-06-02` 及之后 |
| 2026-06-03 | `2026-06-03` 之前 | `2026-06-03` 及之后 |

模型评估时应同时记录：

- 总体准确率或目标指标。
- 各预测日指标。
- 各雨强等级指标。
- 使用的特征版本、坐标版本和数据截止时间。

## 11. 小雨、中雨、暴雨分层评估

降水量数据到位后，按雨强分层统计预测准确率。

建议分层：

| 分层 | 说明 |
|---|---|
| 小雨 | 轻量降水场景 |
| 中雨 | 中等降水场景 |
| 暴雨 | 强降水和高风险场景 |

展示口径：

- 预测结果页或地图图层按雨强分层展示准确率。
- 颜色由浅到深表示雨强或风险等级增强。
- 具体雨量阈值以后续接入的数据源标准或气象部门标准为准，不在当前文档中硬编码。

## 12. 后续更新项

需要同步的项目文档：

- `.env.example`：只保留 `AMAP_WEB_SERVICE_KEY`，移除前端 JS Key 和安全密钥示例。
- `docs/superpowers/plans/2026-06-25-day-2-engineering-setup.md`：更新高德配置口径。
- `PROJECT_OVERVIEW.md`：更新当前成果、下一步工作和高德使用方式。
- `data/README.md`：补充核心表时间范围、坐标缺口和水库未匹配测站结论。

暂不需要修改：

- `PROJECT_STRUCTURE.md`：当前已经包含降水量、6 月滚动测试、坐标来源和审核状态等主线口径。
- `.env`：真实 Key 已存在，不改动、不输出。
