# Day 12 前端闭环验收与算法前置准备

> 日期：2026-07-05  
> 交付物：前端闭环验收版、演示脚本、算法输入字段清单

## 1. 今日结论

Day 12 在 Day 11 首页演示闭环基础上，完成五个前端页面的联调收口和文档验收材料。

核心结论：

- `/` 首页保持 Day 11 能力，不新增地图 SDK，不调用 `/api/map/districts`。
- `/points/:stationCode` 点位详情可展示当前水位、观测时间、风险、趋势、已审核坐标和历史曲线。
- `/data-status` 数据状态页兼容后端实际时间范围字段，能清楚展示导入批次、数据新鲜度、历史快照和水库状态摘要边界。
- `/locations` 坐标校核页保持单点候选生成和审核流程；审核通过后首页和详情页坐标状态一致。
- `/assessments` 规则研判页支持风险/趋势组合筛选，并支持从其它页面携带 `stationCode` 跳转后高亮目标行。
- 五个页面均具备 loading、empty、error 状态，接口失败不白屏。
- 算法前置只整理输入字段、来源接口和限制，不接入预测、降雨或机器学习。

## 2. 页面闭环

| 页面 | Day 12 收口点 |
|---|---|
| 首页 `/` | 回归检查地图散点、点位抽屉、风险摘要、高风险列表、坐标状态和历史快照 |
| 点位详情 `/points/:stationCode` | 历史曲线档位文案改为最近记录条数；空态和错误态清楚；已审核坐标正常展示 |
| 数据状态 `/data-status` | 修正 `observed_at_min/observed_at_max` 字段兼容；坐标候选/审核数量从坐标状态接口读取 |
| 坐标校核 `/locations` | 候选生成、通过/拒绝、503 高德 Key 提示、审核后刷新 |
| 规则研判 `/assessments` | 全市表格、风险/趋势筛选、规则说明全文、目标站点高亮 |

## 3. 验证记录

已运行：

```bash
cd /Users/gjt/Documents/6.22/frontend
npm run test:command-map
npm run build

cd /Users/gjt/Documents/6.22
.venv/bin/python -m unittest tests.test_backend_day5 tests.test_backend_day7 tests.test_backend_day9_hardening
```

结果：

- `npm run test:command-map`：通过。
- `npm run build`：通过；保留 Vite CJS deprecation 和 ECharts 首包大于 500KB 警告。
- 后端 Day 5 / Day 7 / Day 9 回归：21 tests OK。

## 4. 边界

Day 12 未做以下工作：

- 未接入真实高德 JS SDK。
- 未调用 `/api/map/districts`。
- 未接入预测接口。
- 未接入降雨功能。
- 未接入机器学习。
- 未做全量坐标补全。
- 未在前端写入高德 Key。

## 5. 算法前置输入字段清单

本节为 Day 13 算法一期特征工程准备字段口径。当前只整理可用输入、来源接口和限制，不接入预测接口，不实现机器学习。

### 5.1 可用主线字段

| 字段 | 含义 | 来源接口 | 备注 |
|---|---|---|---|
| `station_code` | 测站编码 | `/api/map/points`、`/api/points/{stationCode}`、`/api/points/{stationCode}/history`、`/api/assessments` | 后续特征聚合主键 |
| `station_name` | 测站名称 | 同上 | 展示和人工校核用 |
| `station_type` | 测站类型 | `/api/map/points`、`/api/points/{stationCode}` | 算法一期只使用 `内涝水情站` 主线 |
| `observed_at` / `latest_observed_at` | 水位观测时间 | `/api/points/{stationCode}/history`、`/api/map/points`、`/api/assessments` | 时间序列排序和观测间隔计算 |
| `water_level_m` / `latest_water_level_m` | 水位，单位米 | 同上 | 空值保留但不参与有效水位特征 |
| `raw_water_level` | 原始水位文本 | `/api/map/points`、`/api/points/{stationCode}`、`/api/points/{stationCode}/history` | 追溯和异常排查 |

### 5.2 可派生水位特征

| 特征 | 计算来源 | Day 13 建议 |
|---|---|---|
| 最近有效水位 | 单点历史序列 | 取最近一条 `water_level_m IS NOT NULL` |
| 相邻水位变化量 | 单点历史序列 | `current_water_level_m - previous_water_level_m` |
| 单位时间变化速度 | 单点历史序列 | 水位变化量除以相邻观测秒差 |
| 连续上升/下降次数 | 单点历史序列 | 最近有效序列方向计数 |
| 历史最大/均值 | 单点历史序列 | 按站点聚合，先用全量历史基线 |
| 观测间隔 | 单点历史序列 | 相邻 `observed_at` 秒差 |

### 5.3 规则研判字段

| 字段 | 含义 | 来源接口 | 用途 |
|---|---|---|---|
| `risk_level` | 规则风险等级 | `/api/assessments`、`/api/points/{stationCode}/assessment` | 算法一期可作为规则基线或标签参考 |
| `trend` | 规则趋势提示 | 同上 | 可与水位速度特征对照 |
| `rule_version` | 规则版本 | 同上 | 记录样本生成口径 |
| `rule_description` | 规则说明 | 同上 | 可解释输出参考 |
| `generated_at` | 研判生成时间 | 同上 | 追踪研判生成批次 |

### 5.4 坐标与质量字段

| 字段 | 含义 | 来源接口 | 限制 |
|---|---|---|---|
| `has_coordinates` | 是否有可上图坐标 | `/api/map/points`、`/api/points/{stationCode}` | 只有审核通过坐标可进入地图 |
| `longitude` / `latitude` | 经度 / 纬度 | 同上 | 当前主要来自高德候选审核结果 |
| `coord_source` | 坐标来源 | 同上 | 当前可为 `amap`，不能等同政府标准坐标 |
| `coord_quality` | 坐标质量 | 同上 | 审核通过后为 `verified` |
| `review_status` | 人工审核状态 | 同上、`/api/locations/{stationCode}/candidates` | `pending` 和 `rejected` 不进入地图主线 |

### 5.5 数据状态字段

| 字段 | 含义 | 来源接口 | 用途 |
|---|---|---|---|
| `flood_water_levels.observed_at_min` | 积涝点最早观测时间 | `/api/data/time-range`、`/api/status/data` | 判断训练窗口起点 |
| `flood_water_levels.observed_at_max` | 积涝点最新观测时间 | 同上 | 判断训练窗口终点 |
| `flood_water_levels.record_count` | 积涝点记录数 | `/api/status/data` | 样本规模说明 |
| `data_freshness.status` | 数据新鲜度 | `/api/status/data` | 当前为历史快照 |
| `latest_imported_at` | 最近导入时间 | `/api/imports/latest` | 数据批次追溯 |
| `total_row_count` | 最近导入批次总行数 | `/api/imports/latest` | 数据规模说明 |

### 5.6 当前限制

- 当前不接入降雨，因此不能提前感知尚未体现在水位中的降雨冲击。
- 当前不做模型预测，`risk_level` 和 `trend` 只代表规则研判。
- 当前坐标主要是高德候选审核结果，不能等同政府标准坐标。
- 水库水位只作为状态摘要，不进入地图、积水风险主线、历史曲线或算法一期主样本。
- 时间序列切分必须按时间顺序，不能随机切分，避免时间泄漏。
- 空水位记录可用于质量分析，但不参与有效水位变化量和速度计算。

### 5.7 Day 13 建议输入表

Day 13 可先生成一张按站点和观测时间排序的特征表，最小字段如下：

```text
station_code
station_name
observed_at
water_level_m
previous_observed_at
previous_water_level_m
water_level_delta_m
seconds_since_previous
water_level_velocity_m_per_s
recent_valid_level_m
consecutive_rising_count
consecutive_falling_count
risk_level_rule_v1
trend_rule_v1
has_coordinates
coord_source
coord_quality
review_status
```

## 6. Day 13 衔接

Day 13 可进入算法一期启动：基于现有积涝点历史水位序列整理特征工程模块，优先生成最近水位、相邻变化量、单位时间变化速度、连续上升/下降、历史统计和观测间隔等字段。坐标字段只作为质量和空间辅助字段，不应强依赖全量坐标补齐。
