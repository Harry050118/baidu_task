# Day 9 后端测试与加固交付说明

> 日期：2026-07-02  
> 交付物：前端 API 合同文档、后端加固测试、数据库不可用错误口径

## 1. 今日结论

Day 9 在 Day 4 至 Day 8 后端接口基础上完成联调前收口，重点是测试与文档加固，不新增业务能力。

核心结论：

- 新增前端联调用 API 合同文档：`docs/api/day-9-frontend-api-contract.md`。
- 新增 Day 9 集中加固测试：`tests/test_backend_day9_hardening.py`。
- 后端新增 `create_app()` 应用工厂，便于用不同配置测试服务启动和依赖异常。
- 数据库不可用或 SQLite 访问异常时统一返回 `503`，响应为 `{"detail":"database unavailable"}`，不暴露本地数据库路径或 traceback。
- 坐标候选接口继续在缺少 `AMAP_WEB_SERVICE_KEY` 时返回 `503`，响应不泄露 Key、完整请求 URL 或 `key=` 参数。
- `reservoir_water_levels` 仍只作为状态/质量摘要出现，不进入地图点位、点位详情、历史、统计风险主线或规则研判。
- 当前不实现 `/api/map/districts`，合同文档已明确该接口暂不可联调。

## 2. 新增 API 合同文档

文档路径：

```text
docs/api/day-9-frontend-api-contract.md
```

覆盖接口：

| 接口 | 用途 |
|---|---|
| `GET /health` | 服务和数据库健康检查 |
| `GET /api/map/points` | 地图点位列表 |
| `GET /api/points/{station_code}` | 点位详情 |
| `GET /api/points/{station_code}/history` | 单点历史水位 |
| `GET /api/data/time-range` | 数据时间范围 |
| `GET /api/stats/overview` | 全市主线统计 |
| `GET /api/stats/stations` | 站类分布 |
| `GET /api/status/data` | 数据状态和质量摘要 |
| `GET /api/imports/latest` | 最近导入批次 |
| `GET /api/locations/status` | 坐标治理状态 |
| `POST /api/locations/geocode-candidates` | 单点高德候选坐标 |
| `GET /api/locations/{station_code}/candidates` | 单点候选列表 |
| `POST /api/locations/{station_code}/review` | 人工审核候选 |
| `GET /api/assessments` | 全市规则研判 |
| `GET /api/points/{station_code}/assessment` | 单点规则研判 |

合同文档同时说明：

- `404`、`422`、`503` 的错误口径。
- 坐标字段只在审核通过后进入地图点位。
- 水库水位仅作为状态/质量摘要。
- 当前没有行政区边界接口可联调。

## 3. 后端加固

代码变更：

| 文件 | 作用 |
|---|---|
| `backend/app/main.py` | 新增 `create_app()` 应用工厂和数据库不可用异常处理 |
| `tests/test_backend_day9_hardening.py` | 新增 Day 9 合同与错误口径测试 |

加固口径：

- `/health` 正常时仍返回 `status=ok` 和数据库表清单。
- 数据库文件不存在或 SQLite 访问失败时返回 `503`，detail 固定为 `database unavailable`。
- 不把数据库绝对路径、Python traceback 或底层异常文本返回给前端。
- 保留 FastAPI 默认参数校验 `422` 响应。
- 保留既有 `404` detail，例如 `flood station not found`。

## 4. 测试覆盖

新增 Day 9 测试覆盖：

- 服务可导入并通过 `TestClient` 启动。
- `/health` 响应结构稳定。
- 地图、点位详情、历史、数据范围、统计、状态、导入、坐标、研判接口顶层响应结构稳定。
- 不存在点位返回 `404`，detail 为 `flood station not found`。
- 历史 `limit=5001` 返回 `422`。
- 缺少高德 Key 的坐标候选流程返回 `503`，不泄露密钥材料。
- 数据库不可用时 `/health` 返回稳定 `503`。
- 水库数据不进入地图和风险主线。

已运行：

```bash
.venv/bin/python -m unittest tests/test_backend_day9_hardening.py
.venv/bin/python -m unittest discover tests
git diff --check
```

结果：

```text
tests/test_backend_day9_hardening.py: 6 tests OK
unittest discover tests: 48 tests OK
git diff --check: no output
```

## 5. 范围边界

Day 9 不做以下工作：

- 不新增前端页面。
- 不新增业务接口。
- 不做批量高德坐标补全。
- 不调用高德行政区接口。
- 不实现 `/api/map/districts`。
- 不接入降雨、模型预测或机器学习。
- 不修改真实 SQLite 数据。
- 不把 `reservoir_water_levels` 纳入地图点位或积水风险主线。

## 6. 后续衔接

Day 10 可以基于 `docs/api/day-9-frontend-api-contract.md` 搭建 Vue 工程骨架、API 封装和地图容器。前端联调时应优先使用已列明的 Day 4-8 接口，不依赖当前尚未实现的行政区边界或模型预测接口。
