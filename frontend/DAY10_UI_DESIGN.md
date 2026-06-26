# Day 10 前端 UX/UI 最终方案

> 深圳市积水监测与预测系统  
> 基准：`docs/api/day-9-frontend-api-contract.md`  
> 日期：2026-07-03

---

## 一、设计系统

### Color Tokens

```css
--bg-base:        #0D1117;
--bg-surface:     #161B22;
--bg-raised:      #1F2937;
--border:         #30363D;
--text-primary:   #E6EDF3;
--text-secondary: #8B949E;
--text-muted:     #484F58;

--risk-danger:    #DA3633;
--risk-warning:   #D29922;
--risk-attention: #9E6A03;
--risk-normal:    #238636;
--risk-no-data:   #484F58;

--trend-rising:      #F85149;
--trend-falling:     #3FB950;
--trend-stable:      #8B949E;
--trend-fluctuating: #E3B341;

--chart-line:     #58A6FF;
```

### Typography

- 正文/标签：`Inter`, `PingFang SC`, `Microsoft YaHei`, `system-ui`
- 水位值/站码/时间/数字列：`JetBrains Mono`, `Consolas`, `monospace`
- 数字启用 `font-variant-numeric: tabular-nums`，防止数值刷新时跳动

### Signature Element

风险等级徽章：4px 左色边 + 极淡背景填充 + 文本。来自防汛信号牌语义，全系统唯一风险表达方式。

```
┌──────────┐
│ ■ 危险   │  ← 左边框 4px #DA3633，背景 rgba(218,54,51,0.12)
└──────────┘
```

### 间距规则

4px 基准格。组件内 `8/12/16px`，区块间 `24/32px`。

---

## 二、视觉定位

专业、克制、高信息密度的深色业务指挥系统。不是营销页，不是炫技大屏。核心体验是"值班人员快速判断哪里有风险、数据是否可信、点位为什么不上图"。

---

## 三、页面清单与核心目标

| # | 页面 | 路由 | Vue 文件 | 核心目标 | 主要 API |
|---|------|------|----------|----------|----------|
| 1 | 指挥地图首页 | `/` | `CommandMap.vue` | 全市积涝点、风险分布、坐标可用性、数据时间一眼可判 | `/api/map/points` `/api/stats/overview` `/api/assessments` `/api/status/data` |
| 2 | 点位详情/历史水位 | `/points/:stationCode` | `PointDetail.vue` | 单点水位、历史曲线、坐标状态、规则说明 | `/api/points/{code}` `/api/points/{code}/history` `/api/points/{code}/assessment` |
| 3 | 数据状态页 | `/data-status` | `DataStatus.vue` | 主线数据时间范围、新鲜度、导入批次、质量摘要 | `/api/status/data` `/api/imports/latest` `/api/data/time-range` `/api/stats/stations` |
| 4 | 坐标校核页 | `/locations` | `LocationReview.vue` | 单点坐标候选生成、人工审核 | `/api/locations/status` `/api/locations/{code}/candidates` `/api/locations/geocode-candidates` `/api/locations/{code}/review` |
| 5 | 规则研判页 | `/assessments` | `AssessmentList.vue` | 全市规则研判，按风险/趋势筛查 | `/api/assessments` |

---

## 四、用户操作流程

```
启动系统
→ 指挥地图首页
  → 查看最新观测时间、积涝点总数、风险摘要、坐标状态
  → 点击已审核坐标点位
    → 右侧点位抽屉（PointDrawer）
      → [查看历史曲线] → PointDetail.vue
      → [查看研判]     → AssessmentList.vue 高亮该点
  → 发现点位缺坐标
    → 导航至坐标校核页
      → 选择测站 → 生成高德候选坐标
      → 人工审核通过/拒绝
      → 审核通过后该点才进入 /api/map/points 输出
  → 数据异常或时间不可信
    → 导航至数据状态页
  → 全市风险排查
    → 导航至规则研判页
```

坐标校核只做单点流程，不做批量。

---

## 五、首页信息架构

```
┌─────────────────────────────────────────────────────────────────────┐
│ 深圳积水监测 | 最新观测: 14:28 | ■历史快照 | [数据状态][坐标校核][研判结果] │
├──────────────────────────────┬──────────────────────────────────────┤
│                              │ 态势摘要                              │
│                              │ 积涝点 312    有坐标 280              │
│  MapWorkspace                │ ■危险  2  ■警戒  8  ■关注 15          │
│  只渲染审核通过坐标点           │ ■正常 255  ■无数据 32                │
│  不调用 /api/map/districts    │                                      │
│  无地图能力时显示占位/散点       │ 高风险点位                            │
│                              │ ■ 危险  南联桥洞  2.34m  ↑上升         │
│                              │ ■ 警戒  布吉立交  1.12m  ↕波动         │
│                              │                                      │
│                              │ 坐标状态：缺失 32    候选 0            │
└──────────────────────────────┴──────────────────────────────────────┘
```

不依赖 `/api/map/districts`。无坐标点不编造位置，只进入右侧坐标状态统计和校核入口。

风险摘要由前端基于 `/api/assessments.items` 聚合生成；`/api/stats/overview` 只提供积涝点数量、最新观测时间、记录数和坐标总体状态等主线事实统计。

---

## 六、关键交互说明

### 地图/空间工作区（MapWorkspace）

- 只渲染 `has_coordinates=true` 且 `coordinate_status=approved` 的点
- 无真实地图能力时渲染散点工作区（SVG 坐标散点或占位说明）
- 高德 Key 不在前端任何位置出现
- 不调用 `/api/map/districts`
- 点击点位 → 右侧 `PointDrawer` 展开，不跳页

### 点位抽屉（PointDrawer）

数据来源：`/api/map/points` 点位条目 + 按需调 `/api/points/{code}/assessment`

```
站名 + 站码
水位值（等宽大字）
■ 风险徽章    趋势指示器
观测时间
─────────────────
坐标来源 / 审核状态
─────────────────
[查看历史曲线]    [查看研判]
```

### 历史水位曲线（WaterLevelChart）

- 默认 `limit=500`，选项：`100 / 500 / 1000 / 5000`
- 空水位（`null`）折线断开，不填 0
- 加载中：骨架屏；`limit=5001` 返回 `422` 时显示「参数超出范围」
- X 轴 `observed_at`，Y 轴 `water_level_m`（单位：米），等宽字体

### 数据状态页

- 三块卡片：`DataRangeCard`（时间范围）、`ImportBatchCard`（导入批次）、`FreshnessTag`（新鲜度）
- `historical_snapshot` → 黄色「历史快照」标签 + 「当前数据为历史导入快照，非实时推送」
- `reservoir_water_levels`：一行摘要「水库数据：仅状态摘要，不参与地图和积水风险主线」，不展开字段
- `source_imports` 无 `status/error`：不展示导入成功/失败字段

### 坐标校核页（单点流程）

```
选择测站
→ 无候选 → [生成高德候选坐标]
    → POST /api/locations/geocode-candidates
    → 展示候选坐标 + 散点预览
→ 有候选 → [通过] → ConfirmDialog → POST review approved
         → [拒绝] → ConfirmDialog → POST review rejected
→ 审核后即时刷新状态
→ 503 → 「高德服务未配置，请联系管理员」
```

### 规则研判页

- 表格：`station_name` / `latest_water_level_m` / `risk_level` 徽章 / `trend` 指示器 / `rule_description`（全文） / `generated_at`
- 顶部筛选：全部 / 危险 / 警戒 / 关注 / 正常 / 无数据
- 表头标注「规则版本：flood_rule_v1」
- `rule_description` 全文展示，不截断

### 错误映射

| 状态码 | 前端展示 |
|---|---|
| `404` | 点位不存在或暂不支持该点位 |
| `422` | 请求参数不合法，请修正后重试 |
| `503` | 后端依赖暂不可用 |
| `503`（高德） | 高德服务未配置，请联系管理员 |

不把后端 `detail` 原文暴露给用户。

---

## 七、风险与状态展示规则

| 后端字段 | 中文文案 | 徽章颜色 | 空间点形状 |
|---|---|---|---|
| `danger` | 危险 | `#DA3633` | 实心圆 |
| `warning` | 警戒 | `#D29922` | 实心圆 |
| `attention` | 关注 | `#9E6A03` | 半实心圆 |
| `normal` | 正常 | `#238636` | 空心圆 |
| `no_data` | 无数据 | `#484F58` | 问号点 |
| `rising` | ↑ 上升 | `#F85149` | SVG 上箭头 |
| `falling` | ↓ 下降 | `#3FB950` | SVG 下箭头 |
| `stable` | → 稳定 | `#8B949E` | SVG 水平箭头 |
| `fluctuating` | ↕ 波动 | `#E3B341` | SVG 波动线 |
| `missing_coordinates` | 坐标缺失 | 红色标签 | — |
| `approved` | 已审核 | 绿色标签 | — |
| `rejected` | 已拒绝 | 灰色标签 | — |
| `pending` | 待审核 | 橙色标签 | 不进地图 |
| `historical_snapshot` | 历史快照 | 黄色标签 | — |

风险和趋势均使用文字 + 颜色 + 图形三重编码，不只依赖颜色。禁止使用 emoji 作为图标。

表格中的箭头符号仅作为文案示意；`TrendIndicator.vue` 实现时使用 SVG 图标 + 文本，不使用 emoji。

---

## 八、组件清单

### 全局基础组件

| 组件 | 职责 |
|---|---|
| `RiskBadge.vue` | 风险等级徽章，props: `level` |
| `TrendIndicator.vue` | 趋势指示器（SVG），props: `trend` |
| `CoordStatusTag.vue` | 坐标来源/状态标签 |
| `FreshnessTag.vue` | 数据新鲜度标签 |
| `SkeletonBlock.vue` | 加载骨架屏，props: `width, height` |
| `ErrorState.vue` | 错误展示，props: `code, message` |
| `EmptyState.vue` | 空数据，props: `message, action?` |
| `ConfirmDialog.vue` | 确认对话框，用于坐标审核操作 |

### 地图与态势组件

| 组件 | 职责 |
|---|---|
| `MapWorkspace.vue` | 适配层：有地图能力时接入真实地图，无时展示散点/占位 |
| `StationMarker.vue` | 点位标记，颜色/形状来自 risk_level |
| `PointDrawer.vue` | 右侧点位抽屉 |
| `OverviewPanel.vue` | 全市事实统计；风险摘要由父页面基于 `/api/assessments` 聚合后传入 |
| `HighRiskList.vue` | 高风险点位列表 |
| `CoordSummary.vue` | 坐标治理摘要条 |

### 页面业务组件

| 组件 | 职责 |
|---|---|
| `WaterLevelChart.vue` | ECharts 历史水位折线图 + 骨架屏 |
| `AssessmentTable.vue` | 研判表格 + 风险筛选 |
| `ImportBatchCard.vue` | 最近导入批次卡片 |
| `DataRangeCard.vue` | 主线数据时间范围卡片 |
| `LocationReviewPanel.vue` | 候选坐标展示 + 审核操作 |

---

## 九、Wireframe 草图

### 指挥地图首页

```
┌ 深圳积水监测 | 最新观测 14:28 | ■历史快照 | [数据状态][坐标校核][研判结果] ┐
├──────────────────────────────┬────────────────────────────────────────┤
│                              │ 积涝点 312     有坐标 280               │
│                              │ ■危险 2  ■警戒 8  ■关注 15              │
│  MapWorkspace                │ ■正常 255  ■无数据 32                   │
│  ●危险  ●警戒  ◐关注  ○正常  │                                         │
│  只渲染审核通过点              │ 高风险点位                               │
│                              │ ■ 危险  南联桥洞  2.34m  ↑上升           │
│                              │ ■ 警戒  布吉立交  1.12m  ↕波动           │
│                              │                                         │
│                              │ 坐标：缺失 32 个   候选 0 个             │
└──────────────────────────────┴────────────────────────────────────────┘
```

### 点位抽屉（PointDrawer）

```
┌ 南联第六工业区桥洞                              × ┐
│ 站码 9281192008                                  │
├──────────────────────────────────────────────────┤
│ 2.34 m                                           │
│ ■ 危险           ↑ 上升                          │
│ 观测时间 2026-07-02 14:28                        │
├──────────────────────────────────────────────────┤
│ 坐标来源: amap（高德临时）  审核状态: 已审核         │
├──────────────────────────────────────────────────┤
│ [查看历史曲线]        [查看研判]                   │
└──────────────────────────────────────────────────┘
```

### 点位详情页（PointDetail）

```
┌ ← 返回地图    南联第六工业区桥洞    ■ 危险    ↑ 上升 ┐
│ 当前水位 2.34m         观测时间 2026-07-02 14:28     │
│ 规则版本: flood_rule_v1                              │
│ 规则说明: 水位 2.34m ≥ 危险阈值 2.0m，触发危险等级    │
├──────────────────────────────────────────────────────┤
│ 历史水位曲线   [100] [500] [1000] [5000]              │
│                                                      │
│ 2.5 ┤          ╭─╮                                  │
│ 2.0 ┤────────╭─╯ ╰──────                            │
│ 1.5 ┤────────╯                                       │
│      └──────────────────────────────                 │
│      01-01  03-01  05-01  07-01                      │
├──────────────────────────────────────────────────────┤
│ 坐标: 114.0471, 22.5431   来源: 高德临时   已审核      │
└──────────────────────────────────────────────────────┘
```

### 数据状态页（DataStatus）

```
┌ 数据状态 ────────────────────────────────────────────┐
│ ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│ │ 积涝点范围    │  │ 最近导入批次  │  │ ■ 历史快照  │ │
│ │ 最早:01-01   │  │ 时间:07-01   │  │ 历史导入快照 │ │
│ │ 最新:07-02   │  │ 记录:12,450  │  │ 非实时推送   │ │
│ │ 总计:980,000 │  │ 批次数:23    │  │             │ │
│ └──────────────┘  └──────────────┘  └─────────────┘ │
├──────────────────────────────────────────────────────┤
│ 水库数据：仅状态摘要，不参与地图和积水风险主线           │
│ 测站坐标：缺失 312 个  候选 0 个  已审核 0 个          │
└──────────────────────────────────────────────────────┘
```

### 坐标校核页（LocationReview）

```
┌ 坐标校核   总数 312   候选 0   已审核 0   已拒绝 0 ──┐
├───────────────────┬──────────────────────────────────┤
│ 测站列表           │ 南联第六工业区桥洞                 │
│ 南联桥洞  ■坐标缺失 │ 站码: 9281192008                 │
│ 布吉立交  ■坐标缺失 │                                  │
│ 龙华立交  ■坐标缺失 │ 候选坐标：无                      │
│ ...               │                                  │
│                   │ [生成高德候选坐标]                  │
│                   │                                  │
│                   │ 生成后显示坐标 + 散点预览 +          │
│                   │ [通过] [拒绝] 按钮                 │
└───────────────────┴──────────────────────────────────┘
```

### 规则研判页（AssessmentList）

```
┌ 规则研判   规则版本: flood_rule_v1 ──────────────────┐
│ [全部] [危险] [警戒] [关注] [正常] [无数据]            │
├──────────┬───────┬──────┬──────┬───────────────────┤
│ 测站      │ 水位   │ 风险  │ 趋势  │ 规则说明            │
├──────────┼───────┼──────┼──────┼───────────────────┤
│ 南联桥洞  │ 2.34m │■危险 │↑上升 │ 水位≥2.0m 触发危险  │
│ 布吉立交  │ 1.12m │■警戒 │↕波动 │ 水位≥1.0m 触发警戒  │
└──────────┴───────┴──────┴──────┴───────────────────┘
```

---

## 十、Day 10 Vue 工程骨架

### 目录结构

```
frontend/
├── index.html
├── vite.config.ts
├── tsconfig.json
├── package.json
└── src/
    ├── main.ts
    ├── router/
    │   └── index.ts
    ├── api/
    │   ├── client.ts           # axios 实例 + 错误拦截
    │   ├── health.ts           # GET /health
    │   ├── map.ts              # getMapPoints()
    │   ├── points.ts           # getPoint() / getHistory() / getAssessment()
    │   ├── stats.ts            # getOverview() / getStations()
    │   ├── status.ts           # getDataStatus() / getTimeRange() / getLatestImport()
    │   ├── locations.ts        # getLocationsStatus() / getCandidates() / geocode() / review()
    │   └── assessments.ts      # getAssessments()
    ├── types/
    │   └── api.ts              # 严格对应 Day 9 合同字段的 TS 类型
    ├── stores/
    │   ├── mapPoints.ts        # 点位列表、选中点位
    │   ├── overview.ts         # 统计摘要
    │   └── locations.ts        # 坐标治理状态
    ├── views/
    │   ├── CommandMap.vue
    │   ├── PointDetail.vue
    │   ├── DataStatus.vue
    │   ├── LocationReview.vue
    │   └── AssessmentList.vue
    ├── components/
    │   ├── RiskBadge.vue
    │   ├── TrendIndicator.vue
    │   ├── CoordStatusTag.vue
    │   ├── FreshnessTag.vue
    │   ├── SkeletonBlock.vue
    │   ├── ErrorState.vue
    │   ├── EmptyState.vue
    │   ├── ConfirmDialog.vue
    │   ├── MapWorkspace.vue
    │   ├── StationMarker.vue
    │   ├── PointDrawer.vue
    │   ├── OverviewPanel.vue
    │   ├── HighRiskList.vue
    │   ├── CoordSummary.vue
    │   ├── WaterLevelChart.vue
    │   ├── AssessmentTable.vue
    │   ├── ImportBatchCard.vue
    │   ├── DataRangeCard.vue
    │   └── LocationReviewPanel.vue
    └── map/
        ├── adapter.ts          # MapAdapter 接口，禁止在此放 Key
        └── README.md           # 地图安全接入说明
```

### 依赖

```json
{
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.3.0",
    "pinia": "^2.1.0",
    "axios": "^1.7.0",
    "echarts": "^5.5.0",
    "vue-echarts": "^6.7.0"
  },
  "devDependencies": {
    "vite": "^5.3.0",
    "@vitejs/plugin-vue": "^5.0.0",
    "typescript": "^5.4.0"
  }
}
```

不引入大型 UI 组件库。

### 路由

```ts
const routes = [
  { path: '/',                     component: CommandMap },
  { path: '/points/:stationCode',  component: PointDetail },
  { path: '/data-status',          component: DataStatus },
  { path: '/locations',            component: LocationReview },
  { path: '/assessments',          component: AssessmentList },
]
```

### API 客户端口径

```
baseURL: VITE_API_BASE_URL（本地默认 http://localhost:8000）
不封装 /api/map/districts
不封装 /api/predictions
不在任何封装中携带高德 Key 或 key= 参数
503 → 「后端依赖暂不可用」
404 → 「点位不存在或暂不支持该点位」
422 → 「请求参数不合法」
detail 原文不暴露给用户
```

### map/adapter.ts 说明

```
定义 MapAdapter 接口，MapWorkspace 依赖此接口而非具体地图 SDK
当前实现：PlaceholderAdapter（散点/占位）
后续实现：真实地图适配器；是否使用高德 JS API 需另行确认安全接入方案
禁止在 map/ 目录下硬编码任何 Key
```

### Day 10 必须完成

1. Vite + Vue 3 + TypeScript 工程可启动
2. 五个主路由可访问，刷新不丢路由
3. Day 9 合同内全部 API 封装完成
4. `types/api.ts` 核心响应类型完成
5. CSS token 完成（深色指挥系统配色）
6. 主布局、顶部状态栏、导航完成
7. 五个页面空壳，支持 loading / empty / error 状态
8. `GET /health` 联通验证完成
9. `MapWorkspace` 适配层落位；无真实地图时显示占位/散点工作区

---

## 十一、测试计划

| 测试项 | 验证标准 |
|---|---|
| 路由 | 五个页面可直接访问，刷新不丢路由 |
| API 封装 | Day 9 合同内全部接口有封装；不调用 `/api/map/districts` 或预测接口 |
| 错误展示 | `404/422/503` 均有文案；不暴露 `detail` 原文 |
| 地图/散点 | 无坐标点不渲染；无地图能力时显示占位，不空白 |
| 历史曲线 | 空水位断线不填 0；`limit=5001` 显示参数错误提示 |
| 数据状态 | 水库数据只作为一行摘要出现 |
| 风险/趋势 | 文字 + 颜色 + 图形三重编码；无 emoji 图标 |
| 可访问性 | 图标按钮有 `aria-label`；不只依赖颜色传达状态 |
| 文案禁区 | 全系统不出现：模型预测、降雨、机器学习 |
| 联通验证 | `GET /health` 返回 `status: ok` |

---

## 十二、约束确认

| 约束 | 处理方式 |
|---|---|
| `/api/map/districts` 未实现 | 不调用，不渲染行政区边界 |
| `reservoir_water_levels` 仅摘要 | 只在数据状态页一行说明，不进地图/风险/曲线/统计 |
| 高德 Key 不进前端 | JS API Key 后续独立安全方案接入；Web Service Key 仅后端使用 |
| 无坐标点 | 不渲染 Marker，统计面板单独计数「坐标缺失 N 个」 |
| `source_imports` 无 status/error | 数据状态页不展示导入成功/失败字段 |
| `pending`/`rejected` 坐标候选 | 不进地图点位输出，只在坐标校核页可见 |
| 当前阶段无模型预测 | 全系统不出现预测、降雨、机器学习相关文字或功能入口 |
