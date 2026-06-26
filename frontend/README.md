# 深圳积水监测系统 — 前端使用教程

## 环境要求

- Node.js >= 18（推荐通过 nvm 管理）
- 后端服务运行在 `http://localhost:8000`

## 启动顺序

前端数据依赖后端，请按下面顺序启动。复制命令时只复制代码块里的命令，不要把说明文字一起粘到终端。

### 1. 启动后端

打开第一个终端：

```bash
cd /Users/gjt/Documents/6.22
.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

看到类似下面输出表示后端已启动：

```text
Uvicorn running on http://127.0.0.1:8000
```

可选验证：

```bash
curl http://127.0.0.1:8000/health
```

### 2. 启动前端

保持后端终端不要关闭。再打开第二个终端：

```bash
cd /Users/gjt/Documents/6.22/frontend
npm install
npm run dev
```

看到类似下面输出表示前端已启动：

```text
VITE v5.x.x ready
Local: http://localhost:5173/
```

然后访问：

```text
http://localhost:5173/
```

也可以访问：

```text
http://127.0.0.1:5173/
```

开发环境下，`/api/*` 和 `/health` 由 Vite proxy 转发到 `VITE_API_BASE_URL`（默认 `http://localhost:8000`），无跨域问题。

### 3. 常见提示

- 如果终端显示 `zsh: command not found: #`，说明复制时把注释行也粘进去了；这通常不影响后续命令，但建议只复制代码块里的命令。
- `npm install` 如提示 `npm audit` 漏洞，Day 10 本地联调可先忽略；不要直接运行 `npm audit fix --force`，它可能升级依赖并引入破坏性变更。
- `npm install` 如提示 `fsevents` install scripts 未审批，这是 macOS 可选文件监听依赖，当前不阻塞启动。

## 页面导航

| 路由 | 功能 |
|---|---|
| `/` | 指挥地图首页 — 散点工作区 + 风险摘要 + 高风险点位 |
| `/points/:stationCode` | 单点详情 — 当前水位、历史曲线、规则说明 |
| `/data-status` | 数据状态 — 时间范围、导入批次、新鲜度 |
| `/locations` | 坐标校核 — 生成高德候选坐标、人工审核 |
| `/assessments` | 规则研判 — 全市研判表格，支持风险/趋势双重筛选 |

顶部导航栏有"数据状态 / 坐标校核 / 研判结果"三个快捷入口。

## 生产构建

```bash
# 配置生产后端地址（手动创建，不进 git）
echo "VITE_API_BASE_URL=http://your-backend-host" > .env.local

npm run build
# 产物在 dist/ 目录
```

生产环境若前后端不同源部署，后端需要配置 CORS；或通过 Nginx/网关把 `/api` 和 `/health` 反代到后端。

---

## 本次（Day 10）完成的内容

### 工程基础

- Vite 5 + Vue 3 + TypeScript 工程，`vue-tsc --noEmit` 和 `vite build` 通过；存在 ECharts 首包超过 500KB 的构建警告，后续可懒加载优化
- HTML5 history 路由，5 个主路由，刷新不丢路由
- Vite dev proxy 统一代理 `/api/*` 和 `/health`，开发环境通过 proxy 解决跨域（需后端在 `localhost:8000` 或配置 `.env.local`）
- 深色指挥系统 CSS token（`--bg-base`、`--risk-*`、`--trend-*` 等全套变量）
- 字体：正文 Inter/PingFang SC，数字/代码 JetBrains Mono，等宽数字防跳动

### API 封装（`src/api/`）

严格对应 Day 9 合同，共 8 个封装文件：

- `client.ts` — axios 实例 + 错误拦截（404/422/503 统一文案，高德 503 专属提示，不暴露 detail 原文）
- `health.ts` — `GET /health`
- `map.ts` — `GET /api/map/points`
- `points.ts` — 点位详情 / 历史水位 / 单点研判
- `stats.ts` — 概览统计 / 站类统计
- `status.ts` — 数据状态 / 时间范围 / 导入批次
- `locations.ts` — 坐标状态 / 候选查询 / 高德生成 / 人工审核
- `assessments.ts` — 全市规则研判

未封装：`/api/map/districts`（未实现）、预测相关接口（不在范围内）。

### TypeScript 类型（`src/types/api.ts`）

覆盖 Day 9 合同全部响应结构，含联合类型 `RiskLevel`、`Trend`、`CoordinateStatus`、`ReviewStatus`。

### Pinia 状态管理（`src/stores/`）

- `mapPoints` — 点位列表、选中点位、approved 过滤
- `overview` — 概览统计、历史快照标识、最新观测时间
- `locations` — 坐标治理状态

### 全局基础组件（`src/components/`）

| 组件 | 说明 |
|---|---|
| `RiskBadge` | 风险等级徽章（4px 左色边 + 极淡背景） |
| `TrendIndicator` | 趋势指示器（SVG 箭头 + 文字，无 emoji） |
| `CoordStatusTag` | 坐标状态标签（approved / missing / pending / rejected） |
| `FreshnessTag` | 数据新鲜度标签（历史快照 / 实时） |
| `SkeletonBlock` | 加载骨架屏（shimmer 动画） |
| `ErrorState` | 错误展示（含 404/422/503 标准文案） |
| `EmptyState` | 空数据展示 |
| `ConfirmDialog` | 确认对话框（坐标审核操作用） |

### 地图与态势组件

| 组件 | 说明 |
|---|---|
| `MapWorkspace` | SVG 散点工作区（无真实地图 SDK，无 Key） |
| `StationMarker` | 点位标记（危险=实心圆 / 关注=半实心 / 正常=空心 / 无数据=问号） |
| `PointDrawer` | 右侧点位抽屉（水位大字、风险徽章、趋势、坐标状态、跳转按钮） |
| `OverviewPanel` | 态势摘要（积涝点数、坐标数、风险分布聚合自 assessments） |
| `HighRiskList` | 高风险点位列表 |
| `CoordSummary` | 坐标治理摘要条 |
| `map/adapter.ts` | MapAdapter 接口定义，无任何 Key 硬编码 |

### 页面业务组件

| 组件 | 说明 |
|---|---|
| `WaterLevelChart` | ECharts 历史水位折线图（null 断线不填 0，骨架屏，limit 选择） |
| `AssessmentTable` | 研判表格 + 风险/趋势双重筛选 |
| `ImportBatchCard` | 导入批次卡片 |
| `DataRangeCard` | 时间范围卡片 |
| `LocationReviewPanel` | 候选坐标展示 + 通过/拒绝操作（含 ConfirmDialog） |

### 五个页面视图

- **CommandMap** — 散点地图 + 右侧态势面板；assessments `risk_level` 合并到地图点位颜色
- **PointDetail** — 单点水位、规则说明、历史曲线（100/500/1000/5000 档位，422 专属提示）
- **DataStatus** — 三卡片布局（时间范围 / 导入批次 / 新鲜度）+ 水库摘要一行说明
- **LocationReview** — 左侧站点列表 + 右侧单点审核面板，审核后即时刷新
- **AssessmentList** — 研判表格，风险 × 趋势双筛选

### 安全与约束

- 高德 Key 不在任何前端文件中出现
- 不调用 `/api/map/districts` 或任何预测接口
- `pending`/`rejected` 坐标不进地图，只在坐标校核页可见
- 水库数据只作为数据状态页一行摘要
- 全系统不出现"预测、降雨、机器学习"相关文字
- 所有错误文案不暴露后端 `detail` 原文
