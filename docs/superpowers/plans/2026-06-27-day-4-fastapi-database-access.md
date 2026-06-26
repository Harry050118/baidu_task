# Day 4 FastAPI 骨架与数据库访问

> 日期：2026-06-27  
> 交付物：后端可启动服务  
> 提交：`370072b feat: establish monitoring backend baseline`

## 1. 今日目标

Day 4 启动后端监测闭环的工程骨架，只做 FastAPI 服务、配置读取、SQLite 只读访问、健康检查和基础 Repository。

本日不做地图正式 API、坐标补全、风险研判、模型训练或下载归档重跑。

## 2. 已完成内容

- 新增 FastAPI 应用入口：`backend/app/main.py`。
- 新增健康检查接口：`GET /health`。
- 新增配置读取：`backend/app/core/config.py`，默认数据库为 `sqlite:///data/local/shenzhen_water.db`。
- 新增 SQLite 只读连接：`backend/app/core/database.py`。
- 新增基础 Repository：`backend/app/repositories/water_repository.py`。
- 新增最小依赖声明：`requirements.txt`。
- 新增 Day 4 测试：`tests/test_backend_day4.py`。

## 3. Repository 能力

主线围绕 `stations + flood_water_levels`：

- 数据库摘要。
- 积涝点最新水位。
- 单点历史水位。
- 积涝点数据时间范围。
- 测站缺坐标状态。

水库数据只保留质量摘要：

- 水库记录数。
- 水库唯一测站数。
- 空水位记录数。
- 未匹配基础信息的水库测站数。

## 4. 已确认数据事实

| 项目 | 值 |
|---|---:|
| `stations` 行数 | 485 |
| `flood_water_levels` 行数 | 4,101,063 |
| 积涝点唯一测站 | 148 |
| 积涝点测站基础信息匹配 | 148 |
| 积涝点时间范围 | `2025-12-31 23:50:23` 至 `2026-06-23 00:47:39` |
| `reservoir_water_levels` 行数 | 2,040,352 |
| 水库唯一测站 | 178 |
| 水库空水位 | 40,982 |
| 水库未匹配基础信息测站 | 9 |

## 5. 坐标口径

当前 `stations` 表没有经纬度、坐标系、坐标来源、坐标质量或审核状态字段。

Day 4 只输出缺坐标状态，不编造坐标，不批量补坐标，不调用高德 API。

## 6. 验证结果

已运行：

```bash
.venv/bin/python -m unittest discover -s tests
```

结果：

```text
Ran 18 tests
OK
```

已验证：

- `/health` 返回 `200`。
- SQLite 连接为只读，写入会失败。
- Repository 查询结果与 Day 3 数据事实一致。

## 7. Day 5 交接

Day 5 进入“地图与历史 API”：

- `GET /api/map/points`：只返回积涝点，不包含水库点位，不输出虚假坐标。
- `GET /api/points/{station_code}/history`：返回单点积涝水位历史。
- `GET /api/data/time-range`：返回积涝点数据时间范围。
- 点位详情接口：返回测站信息、最新水位和坐标状态。

继续保持：水库只作为数据状态/质量摘要，不进入积涝风险主线。
