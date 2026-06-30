# Day 13 水位特征工程

> 日期：2026-07-06  
> 交付物：算法一期水位特征表、质量检查摘要、特征工程脚本和单元测试

## 1. 今日结论

Day 13 完成离线水位特征工程，基于本地 SQLite 数据库 `data/local/shenzhen_water.db` 的 `flood_water_levels`、`stations` 和可选 `location_candidates`，生成可供后续异常检测、趋势增强、风险评分和模型基线使用的历史水位特征表。

本日未接入预测接口，未训练机器学习模型，未接入降雨数据，未改动前端主流程。

## 2. 生成文件

| 文件 | 说明 |
|---|---|
| `scripts/build_flood_water_level_features.py` | Day 13 离线特征工程脚本 |
| `data/features/flood_water_level_features_day13.csv` | 水位特征表，共 4,101,063 条记录，约 520MB |
| `data/features/flood_water_level_features_day13_quality.json` | 特征生成质量检查摘要 |
| `tests/test_build_flood_water_level_features.py` | 特征计算和质量摘要单元测试 |

运行命令：

```bash
.venv/bin/python scripts/build_flood_water_level_features.py \
  --db data/local/shenzhen_water.db \
  --output data/features/flood_water_level_features_day13.csv \
  --quality-output data/features/flood_water_level_features_day13_quality.json
```

## 3. 特征字段

| 字段 | 含义 |
|---|---|
| `station_code` | 测站编码，特征主键之一 |
| `station_name` | 测站名称，来自 `stations` |
| `observed_at` | 当前水位观测时间 |
| `water_level_m` | 当前水位，单位米 |
| `previous_observed_at` | 同站点上一条有效水位观测时间 |
| `previous_water_level_m` | 同站点上一条有效水位 |
| `water_level_delta_m` | 当前有效水位减上一条有效水位 |
| `seconds_since_previous` | 当前有效观测与上一条有效观测的秒差 |
| `water_level_velocity_m_per_s` | 水位变化量除以秒差；秒差小于等于 0 时留空 |
| `recent_valid_level_m` | 当前行之前或当前行可见的最近有效水位 |
| `consecutive_rising_count` | 连续上升次数，遇到下降或持平重置 |
| `consecutive_falling_count` | 连续下降次数，遇到上升或持平重置 |
| `has_coordinates` | 是否存在已审核坐标候选 |
| `coord_source` | 坐标来源，例如 `amap` |
| `coord_quality` | 坐标质量，例如 `verified` |
| `review_status` | 坐标审核状态，当前只关联 `approved` 坐标 |
| `risk_level_rule_v1` | 复用规则研判水位阈值输出的风险等级 |
| `trend_rule_v1` | 复用最近有效水位序列输出的规则趋势 |

## 4. 质量检查结果

| 指标 | 数值 |
|---|---:|
| 总记录数 | 4,101,063 |
| 站点数 | 148 |
| 空水位数量 | 0 |
| 0 水位数量 | 3,159,438 |
| 非 0 水位数量 | 941,625 |
| 时间间隔异常数量 | 212,739 |
| 瞬时跳变候选数量 | 47 |
| 每站最小样本量 | 4,362 |
| 每站 P25 样本量 | 9,475 |
| 每站中位样本量 | 29,011 |
| 每站 P75 样本量 | 35,571 |
| 每站最大样本量 | 86,001 |
| 每站平均样本量 | 27,709.89 |

质量阈值：

- 时间间隔异常：`seconds_since_previous <= 0` 或 `seconds_since_previous > 21600`。
- 瞬时跳变候选：`abs(water_level_delta_m) >= 0.20` 且 `0 < seconds_since_previous <= 3600`。

## 5. 限制说明

- 当前无降雨特征，不能提前感知尚未体现在水位序列中的降雨冲击。
- 当前只生成特征，不训练模型，不能称为预测结果。
- 当前坐标不完整，只有已审核候选坐标进入特征质量字段；缺坐标不影响水位特征生成。
- 高德候选坐标不能等同政府标准坐标，后续标准坐标到位后需要重新生成空间相关特征。
- 规则字段 `risk_level_rule_v1` 和 `trend_rule_v1` 仅为后续关联和对照预留，不代表机器学习输出。

## 6. Day 14 建议

Day 14 可在本特征表基础上实现异常检测与趋势增强：优先处理空值、长时间未更新、重复/非正间隔、瞬时跳变候选和趋势解释文本，再输出可被风险评分使用的异常标记表。
