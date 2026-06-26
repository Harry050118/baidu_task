# Day 10 前端工程骨架交付说明

> 日期：2026-07-03  
> 交付物：Vue 3 前端工程骨架、全部页面视图、API 封装、组件库、联调配置

## 1. 今日结论

Day 10 基于 Day 9 前端 API 合同文档，完成深圳积水监测与预测系统的 Vue 3 前端工程骨架。

核心结论：

- Vite 5 + Vue 3 + TypeScript 工程可启动，`vue-tsc --noEmit` 和 `vite build` 通过。
- 5 个主路由可访问，HTML5 history 模式，刷新不丢路由。
- Day 9 合同内全部 15 个 API 接口封装完成；`/api/map/districts` 和预测接口不封装。
- `types/api.ts` 覆盖 Day 9 合同全部响应类型。
- 深色指挥系统 CSS token 落地（`--bg-base`、`--risk-*`、`--trend-*` 等全套变量）。
- 21 个组件全部创建，含骨架屏、错误/空状态、风险徽章、趋势指示器、地图散点工作区等。
- 五个页面视图完成，含 loading / empty / error 三态处理。
- 开发环境通过 Vite proxy 代理 `/api/*` 和 `/health`，无跨域问题。
- 地图点位颜色由 `/api/assessments` 的 `risk_level` 合并驱动，不全量默认 `no_data`。
- 高德 Key 不在任何前端文件中出现，不调用 `/api/map/districts` 或预测接口。

## 2. 页面清单

| 页面 | 路由 | Vue 文件 | 核心功能 |
|---|---|---|---|
| 指挥地图首页 | `/` | `CommandMap.vue` | SVG 散点工作区、风险摘要、高风险列表、点位抽屉 |
| 点位详情 | `/points/:stationCode` | `PointDetail.vue` | 当前水位、历史曲线、规则说明、坐标状态 |
| 数据状态 | `/data-status` | `DataStatus.vue` | 时间范围、导入批次、新鲜度标签、水库摘要 |
| 坐标校核 | `/locations` | `LocationReview.vue` | 单点流程：生成高德候选、通过/拒绝审核 |
| 规则研判 | `/assessments` | `AssessmentList.vue` | 全市研判表格，风险 × 趋势双重筛选 |

## 3. 工程目录

```
frontend/
├── index.html
├── vite.config.ts          # Vite proxy: /api/* 和 /health → localhost:8000
├── package.json
├── tsconfig.json
└── src/
    ├── main.ts
    ├── style.css           # CSS token 全套深色变量
    ├── App.vue             # 顶栏：品牌名、最新观测时间、历史快照标签、健康状态圆点、导航
    ├── vite-env.d.ts
    ├── router/index.ts
    ├── api/                # 8 个封装文件
    ├── types/api.ts
    ├── stores/             # mapPoints / overview / locations
    ├── views/              # 5 个页面
    ├── components/         # 21 个组件
    └── map/adapter.ts      # MapAdapter 接口，无任何 Key
```

## 4. API 封装

严格对应 Day 9 合同，共 8 个封装文件：

| 文件 | 覆盖接口 |
|---|---|
| `client.ts` | axios 实例 + 错误拦截（404/422/503 统一文案，高德 503 专属提示） |
| `health.ts` | `GET /health` |
| `map.ts` | `GET /api/map/points` |
| `points.ts` | 点位详情 / 历史水位 / 单点研判 |
| `stats.ts` | 概览统计 / 站类统计 |
| `status.ts` | 数据状态 / 时间范围 / 导入批次 |
| `locations.ts` | 坐标状态 / 候选查询 / 高德生成 / 人工审核 |
| `assessments.ts` | 全市规则研判 |

不封装 `/api/map/districts`（未实现）、`/api/predictions`（不在范围内）。

## 5. 组件清单

### 全局基础组件

| 组件 | 职责 |
|---|---|
| `RiskBadge` | 风险等级徽章（4px 左色边 + 极淡背景，无 emoji） |
| `TrendIndicator` | 趋势指示器（SVG 图标 + 文字，无 emoji） |
| `CoordStatusTag` | 坐标状态标签（approved / missing / pending / rejected） |
| `FreshnessTag` | 数据新鲜度标签（历史快照 / 实时） |
| `SkeletonBlock` | 加载骨架屏（shimmer 动画） |
| `ErrorState` | 错误展示，含 404/422/503 标准文案，不暴露 detail 原文 |
| `EmptyState` | 空数据展示，支持操作按钮 |
| `ConfirmDialog` | 确认对话框（坐标审核用，Teleport 挂载） |

### 地图与态势组件

| 组件 | 职责 |
|---|---|
| `MapWorkspace` | SVG 散点工作区，只渲染 `approved` 坐标点 |
| `StationMarker` | 点位标记（危险=实心圆 / 关注=半实心 / 正常=空心 / 无数据=问号） |
| `PointDrawer` | 右侧点位抽屉（水位大字、风险徽章、趋势、坐标状态、跳转链接） |
| `OverviewPanel` | 态势摘要（风险分布聚合自 `/api/assessments`） |
| `HighRiskList` | 高风险点位列表（danger + warning） |
| `CoordSummary` | 坐标治理摘要条 |

### 页面业务组件

| 组件 | 职责 |
|---|---|
| `WaterLevelChart` | ECharts 历史水位折线（null 断线不填 0，limit 四档） |
| `AssessmentTable` | 研判表格 + 风险/趋势双重筛选 |
| `ImportBatchCard` | 最近导入批次卡片 |
| `DataRangeCard` | 主线数据时间范围卡片 |
| `LocationReviewPanel` | 候选坐标展示 + 通过/拒绝操作 |

## 6. 关键实现细节

**地图点位风险颜色**：`CommandMap.vue` 在渲染前将 `/api/assessments` 返回的 `risk_level` 按 `station_code` 合并到地图点位，避免全量显示为无数据样式。

**历史水位曲线**：`connectNulls: false`，null 值折线断开，不填 0；`limit=5001` 返回 422 时显示专属提示，而非通用错误文案。

**坐标校核单点流程**：生成 → 展示候选 → 确认弹窗 → 审核 → 即时刷新状态；503 响应专属显示"高德服务未配置，请联系管理员"。

**健康检查**：`App.vue` `onMounted` 时同步调用 `/health`，顶栏右侧显示 8px 状态圆点（绿/红/灰），同时触发 `overviewStore.load()`，确保任意页面直接进入时顶栏数据可用。

**趋势筛选**：`AssessmentTable` 风险和趋势两个筛选条件独立且可组合，支持"危险 × 上升"等交叉过滤。

## 7. 验证结果

```text
vue-tsc --noEmit:   通过（0 类型错误）
vite build:         通过（存在 ECharts 首包超 500KB 构建警告，后续可懒加载优化）
/api/map/points:    返回 148 个点，其中 5 个审核坐标点可进入散点工作区
/api/assessments:   返回 148 条规则研判
/health:            返回 {"status":"ok"}（后端运行时）
```

本地实测 `/api/map/points` 响应约 8.5 秒，Day 11 需优化后端查询或分区加载。

## 8. 范围边界

Day 10 不做以下工作：

- 不接入真实地图 SDK（无高德 JS API Key）
- 不调用 `/api/map/districts`
- 不新增后端接口
- 不接入降雨、模型预测或机器学习
- 不做批量坐标补全
- 不做前端权限/登录
- `reservoir_water_levels` 只在数据状态页一行摘要，不进地图/风险/曲线/统计

## 9. 后续衔接（Day 11+）

- 优化 `/api/map/points` 响应时间（目标 < 1s）
- 接入真实地图 SDK（安全 Key 注入方案需独立确认）
- "查看研判并高亮该点"：从 `PointDrawer` 跳转时携带 `stationCode`，研判页高亮目标行
- ECharts 懒加载，减小首包体积
- 生产环境 CORS 或反代方案确认
