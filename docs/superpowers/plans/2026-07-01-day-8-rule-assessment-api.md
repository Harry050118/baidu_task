# Day 8 规则研判服务 API 交付说明

> 日期：2026-07-01  
> 交付物：全市规则研判、单点规则研判、风险等级和趋势提示 API

## 1. 今日结论

Day 8 在 Day 5 地图与历史 API、Day 6 统计与状态 API、Day 7 坐标候选与审核 API 基础上，完成规则研判服务的最小后端闭环。

核心结论：

- 新增 `/api/assessments`，返回全市 148 个积涝点规则研判结果。
- 新增 `/api/points/{station_code}/assessment`，返回单个积涝点规则研判结果。
- 规则研判只使用 `stations + flood_water_levels`。
- `reservoir_water_levels` 不进入积水风险研判主线。
- 坐标审核状态不影响规则研判；未审核坐标仍不会进入 `/api/map/points`。
- Day 8 不做模型预测、不做机器学习、不接入降雨、不回写数据库。
- 当前规则版本为 `flood_rule_v1`。

## 2. 新增 API

### 2.1 `GET /api/assessments`

用途：为前端研判面板或地图弹窗提供全市积涝点风险等级和趋势提示。

返回口径：

| 字段 | 说明 |
|---|---|
| `station_code` | 测站编码 |
| `station_name` | 测站名称 |
| `latest_observed_at` | 最新有效积涝水位观测时间 |
| `latest_water_level_m` | 最新有效积涝水位，单位米 |
| `risk_level` | 风险等级 |
| `trend` | 趋势提示 |
| `rule_version` | 规则版本 |
| `rule_description` | 规则说明 |
| `generated_at` | 研判生成时间 |

说明：

- 返回 `items` 列表。
- 当前只返回积涝点，不返回水库测站。
- 响应不包含 `reservoir_water_levels`。

### 2.2 `GET /api/points/{station_code}/assessment`

用途：返回单个积涝点的规则研判结果。

错误口径：

- `station_code` 不存在：`404`
- `station_code` 存在但不是积涝点：`404`
- 错误信息：`flood station not found`

## 3. 规则口径

### 3.1 风险等级

风险等级基于最新有效积涝点水位统一阈值计算。

| 风险等级 | 条件 |
|---|---|
| `no_data` | 无有效水位 |
| `normal` | `water_level_m < 0.15` |
| `attention` | `0.15 <= water_level_m < 0.30` |
| `warning` | `0.30 <= water_level_m < 0.50` |
| `danger` | `water_level_m >= 0.50` |

### 3.2 趋势提示

趋势提示基于最近 6 条有效积涝水位序列计算。

| 趋势 | 条件 |
|---|---|
| `no_data` | 无有效水位 |
| `stable` | 单条数据，或序列极差 `<= 0.02m` |
| `rising` | 序列整体连续上升 |
| `falling` | 序列整体连续下降 |
| `fluctuating` | 不满足稳定、连续上升或连续下降 |

## 4. 代码变更

| 文件 | 作用 |
|---|---|
| `backend/app/services/assessments.py` | 规则研判函数、规则版本和输出结构 |
| `backend/app/api/routes.py` | 新增全市和单点研判 API |
| `backend/app/repositories/water_repository.py` | 新增积涝站列表和最近有效水位序列查询 |
| `tests/test_backend_day8.py` | Day 8 API 和规则测试 |

## 5. 测试覆盖

新增测试文件：

```text
tests/test_backend_day8.py
```

覆盖重点：

- 服务可启动，既有 `/health` 未回退。
- `/api/assessments` 返回 148 个积涝点。
- `/api/points/9281192008/assessment` 对真实积涝点可用。
- 不存在测站或非积涝点测站返回 `404`。
- 风险等级阈值覆盖 `no_data`、`normal`、`attention`、`warning`、`danger`。
- 趋势规则覆盖 `no_data`、`stable`、`rising`、`falling`、`fluctuating`。
- 水库水位不进入主线风险输出。

已运行：

```bash
.venv/bin/python -m unittest tests/test_backend_day8.py
.venv/bin/python -m unittest discover tests
git diff --check
```

结果：

```text
tests/test_backend_day8.py: 6 tests OK
unittest discover tests: 42 tests OK
git diff --check: no output
```

## 6. 后续衔接

Day 8 不做以下工作：

- 不做模型预测。
- 不做机器学习。
- 不接入降雨数据。
- 不回写研判结果表。
- 不把水库水位纳入积水风险主线。
- 不扩展 `/api/map/points` 风险字段。

后续 Day 9 可继续做后端测试加固、接口文档整理和前端联调前的异常响应检查。
