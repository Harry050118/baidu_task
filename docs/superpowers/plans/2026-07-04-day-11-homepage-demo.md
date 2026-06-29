# Day 11 前端首页演示级交付说明

> 日期：2026-07-04  
> 交付物：首页演示闭环、点位抽屉、高风险列表、坐标状态说明、验收清单

## 1. 今日结论

Day 11 在 Day 10 前端骨架基础上，把指挥地图首页补到可演示状态。

核心结论：

- 首页自动加载 `/health`、`/api/map/points`、`/api/assessments`、`/api/stats/overview`。
- 首页具备 loading、empty、error 状态，接口失败不白屏。
- 风险摘要由 `/api/assessments.items` 前端聚合，`/api/stats/overview` 只用于事实统计。
- 地图只渲染已有审核坐标的点位，缺坐标点不编造、不落图。
- 首页明确展示有坐标点数量、缺坐标点数量、最新观测时间和历史快照状态。
- 点位可点击，右侧抽屉展示站名、站码、水位、风险、趋势、观测时间、坐标状态和坐标来源。
- 高风险列表展示 `danger`、`warning`、`attention` 点位；无高风险时显示专业空态。
- 新增 Day 11 首页验收清单。

## 2. 主要变更

| 文件 | 说明 |
|---|---|
| `frontend/src/views/CommandMap.vue` | 首页数据加载、错误兜底、点位选择和高风险列表联动 |
| `frontend/src/components/MapWorkspace.vue` | 散点工作区、参考底图、loading/empty/error |
| `frontend/src/components/StationMarker.vue` | 点位改为外环加实心圆心，扩大点击热区 |
| `frontend/src/components/OverviewPanel.vue` | 事实统计、风险摘要、数据覆盖范围和历史快照 |
| `frontend/src/components/PointDrawer.vue` | 点位抽屉信息补齐和跳转入口 |
| `frontend/src/components/HighRiskList.vue` | 高风险排序、空态、列表项字段补齐 |
| `frontend/src/components/CoordSummary.vue` | 地图可见点、缺坐标点、候选坐标摘要 |
| `frontend/src/utils/commandMap.ts` | 首页聚合、过滤、排序和时间范围格式化逻辑 |
| `frontend/FRONTEND_ACCEPTANCE_CHECKLIST.md` | Day 11 首页验收清单 |

另外修复了点位详情接口和页面字段口径：

- `GET /api/points/{station_code}` 现在会返回已审核坐标。
- 点位详情页兼容 `latest_water_level_m/latest_observed_at` 字段。

## 3. 当前首页能力

- 可以看到后端健康状态。
- 可以看到最新观测时间和数据覆盖范围。
- 可以看到历史快照标识。
- 可以看到积涝点数、记录数、有坐标点数、缺坐标点数。
- 可以看到规则研判聚合出的风险分布。
- 可以点击地图点位打开抽屉。
- 可以从抽屉跳转历史曲线和研判页。
- 缺坐标点不会出现在地图上，但会在右侧统计中说明。

## 4. 验证结果

已运行：

```bash
cd frontend && npm run test:command-map
cd frontend && npm run build
.venv/bin/python -m unittest tests.test_backend_day5 tests.test_backend_day7 tests.test_backend_day9_hardening
```

结果：

```text
npm run test:command-map: 通过
npm run build: 通过
后端相关测试: 21 tests OK
```

构建仍有 Vite CJS deprecation 和 chunk size warning，不阻塞 Day 11 交付。

## 5. 范围边界

Day 11 不做以下工作：

- 不接入真实高德 JS SDK。
- 不调用 `/api/map/districts`。
- 不做预测、降雨或机器学习功能。
- 不做全量坐标补全。
- 不在前端写入高德 Key。

## 6. 后续衔接

Day 12 建议：

- 完成点位详情、历史曲线、数据状态、坐标校核、研判页的完整联调。
- 统一各页面异常态。
- 整理前端演示脚本。
- 根据 `FRONTEND_ACCEPTANCE_CHECKLIST.md` 做一次人工验收勾选。
