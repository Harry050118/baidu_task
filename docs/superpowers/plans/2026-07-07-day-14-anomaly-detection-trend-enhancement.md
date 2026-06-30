# Day 14 异常检测与趋势增强

> 日期：2026-07-07  
> 交付物：异常检测结果、趋势增强结果、质量摘要、离线生成脚本和单元测试

## 1. 今日结论

Day 14 基于 Day 13 水位特征表完成离线异常检测与趋势增强，生成了可解释的异常记录、增强趋势标签和质量摘要。今日工作不接入预测接口，不训练机器学习模型，不接入降雨数据，不修改前端主流程。

Day 14 使用 Day 13 的本地特征 CSV 作为主输入：

```text
data/features/flood_water_level_features_day13.csv
data/features/flood_water_level_features_day13_quality.json
```

如果本地特征 CSV 不存在，需要先运行 Day 13 特征工程脚本生成；该大型 CSV 仍只作为本地生成物，不作为代码交付文件。

## 2. 生成文件

| 文件 | 说明 |
|---|---|
| `scripts/build_flood_water_level_anomalies_day14.py` | Day 14 异常检测与趋势增强脚本 |
| `data/features/flood_water_level_anomalies_day14.csv` | 异常检测结果，共 212,790 条记录，约 48MB |
| `data/features/flood_water_level_trends_day14.csv` | 趋势增强结果，共 4,101,063 条记录，约 670MB |
| `data/features/flood_water_level_anomalies_day14_quality.json` | Day 14 质量摘要 |
| `tests/test_build_flood_water_level_anomalies_day14.py` | Day 14 单元测试 |

CSV 输出位于 `data/features/`，已被 `.gitignore` 中的 `data/features/*.csv` 覆盖，不作为交付提交对象。质量摘要 JSON 可用于验收查看。

运行命令：

```bash
.venv/bin/python scripts/build_flood_water_level_anomalies_day14.py \
  --features data/features/flood_water_level_features_day13.csv \
  --day13-quality data/features/flood_water_level_features_day13_quality.json \
  --anomalies-output data/features/flood_water_level_anomalies_day14.csv \
  --trends-output data/features/flood_water_level_trends_day14.csv \
  --quality-output data/features/flood_water_level_anomalies_day14_quality.json
```

## 3. 异常类型定义

| 异常类型 | 阈值/条件 | 严重度 | 说明 |
|---|---|---|---|
| `duplicate_or_non_positive_interval` | `seconds_since_previous <= 0` | high | 重复时间、倒序或非正时间差，变化速度不可解释 |
| `stale_gap` | `seconds_since_previous > 21600` | medium | 同站点长时间未更新 |
| `instant_jump_candidate` | `abs(water_level_delta_m) >= 0.20` 且 `0 < seconds_since_previous <= 3600` | high | 短时间水位大幅变化候选 |
| `short_spike_candidate` | 短时间上升 `>=0.20m` 后又在 `<=3600s` 内回落 `<=-0.20m` | high | 疑似尖峰值候选 |

`insufficient_data` 不进入异常 CSV，只作为趋势增强标签使用。

## 4. 趋势增强标签

| 标签 | 说明 |
|---|---|
| `data_insufficient` | 缺少上一条有效观测、变化量，或秒差为非正值 |
| `long_gap` | 长时间断档，优先于普通趋势解释 |
| `short_spike` | 短时间大幅升高后又快速回落 |
| `rapid_rising` | 短时间快速上升 |
| `sustained_rising` | 同站点连续上升次数达到 2 次及以上 |
| `rapid_falling` | 短时间快速下降 |
| `sustained_falling` | 同站点连续下降次数达到 2 次及以上 |
| `stable` | 水位变化幅度较小或规则趋势稳定 |
| `fluctuating` | 最近有效水位序列呈波动态势 |

趋势增强标签用于解释历史样本和支撑 Day 15 风险评分，不替代 Day 8/Day 12 前端主流程中的规则趋势字段。

## 5. 质量检查结果

| 指标 | 数值 |
|---|---:|
| 异常总数 | 212,790 |
| 涉及站点数 | 148 |
| 高严重度异常 | 212,206 |
| 中严重度异常 | 584 |
| 重复或非正时间差 | 212,155 |
| 长时间断档 | 584 |
| 瞬时跳变候选 | 48 |
| 短时尖峰候选 | 3 |

趋势增强标签分布：

| 标签 | 数量 |
|---|---:|
| `stable` | 3,854,912 |
| `data_insufficient` | 212,303 |
| `fluctuating` | 28,688 |
| `sustained_falling` | 2,540 |
| `sustained_rising` | 1,988 |
| `long_gap` | 584 |
| `rapid_rising` | 24 |
| `rapid_falling` | 21 |
| `short_spike` | 3 |

异常数量最多的站点样例：

| 站点编码 | 异常数 |
|---|---:|
| `9281192005` | 4,561 |
| `9281192003` | 3,764 |
| `MS1104403050000122` | 3,392 |
| `MS1104403050000228` | 3,370 |
| `9281192015` | 3,343 |

高风险样例以重复或非正时间差为主，说明原始序列中存在大量同站点同时间或非正间隔记录。该现象应在 Day 15 风险评分中作为数据质量扣分项，而不是直接等同于积水风险。

## 6. 限制说明

- 当前无降雨特征，不能提前感知尚未体现在水位序列中的降雨冲击。
- 当前只输出异常候选和趋势解释，不训练模型，不能称为预测结果。
- 当前不接预测接口，不改前端主流程，不影响 Day 12 前端闭环。
- 异常检测基于 Day 13 派生特征，若 Day 13 CSV 重新生成，Day 14 结果也应同步重新生成。
- 高德坐标和政府标准坐标不参与 Day 14 异常检测；坐标质量仍按既有数据治理口径单独处理。

## 7. Day 15 建议

Day 15 可在现有规则研判基础上建立风险评分基线，建议输入包括：

- 当前水位风险等级。
- 水位变化速度和快速上升/下降标签。
- 长时间断档和重复时间等数据质量异常。
- 短时尖峰候选，作为质量异常或需复核样本降权。
- 坐标审核状态和数据新鲜度。

风险评分仍应定位为规则基线和排序口径，不训练机器学习模型，不接入预测服务。
