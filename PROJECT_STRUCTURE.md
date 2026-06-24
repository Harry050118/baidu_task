# 项目整体目录规范

本文档说明当前项目目录的作用，以及后续代码落地时建议采用的整体布局。项目目标是建设深圳市积水实时监测地图系统，技术路线暂定为 FastAPI + Vue + 高德地图，一期使用 SQLite 验证数据闭环和轻量预测能力，后续架构预留 PostgreSQL + PostGIS。

## 1. 当前已有目录

```text
.
├── task.md
├── PROJECT_OVERVIEW.md
├── PROJECT_STRUCTURE.md
├── data/
├── docs/
├── download/
├── scripts/
└── tests/
```

### `task.md`

项目原始需求说明，记录系统目标、所需数据、页面成果和预测模型方向。后续需求变更应优先同步到正式设计文档，而不是直接覆盖原始需求。

### `PROJECT_OVERVIEW.md`

项目工程总览，说明项目目标、主线流程、核心模块、支线边界、技术架构、阶段安排和当前成果。该文档适合用于快速理解项目整体脉络。

### `data/`

本地数据目录，用于存放数据库、样本数据和后续地理数据。

```text
data/
├── README.md
├── local/
│   └── shenzhen_water.db
└── raw_samples/
    ├── sample_station_page.html
    └── sample_water_level_page.html
```

- `data/local/shenzhen_water.db`：当前 SQLite 本地数据库，用于一期数据导入和查询验证。
- `data/raw_samples/`：保存接口页面或样本页面，便于离线分析字段和调试解析逻辑。
- 后续建议新增 `data/geo/`，用于存放深圳行政区 GeoJSON 等空间数据。

### `docs/`

项目文档目录。

```text
docs/
├── data_reference.md
└── superpowers/
    ├── specs/
    └── plans/
```

- `docs/data_reference.md`：已确认的数据源、字段映射、本地库说明和已知缺口。
- `docs/superpowers/specs/`：系统设计文档，例如顶层架构、数据库设计、地图前后端设计。
- `docs/superpowers/plans/`：项目计划文档，例如 25 天排期。
- 后续建议新增 `docs/api_reference.md`、`docs/database.md`、`docs/deployment.md`、`docs/user_guide.md`。

### `download/`

开放数据下载归档目录。该目录保存原始分页响应、下载元数据和汇总 CSV。

```text
download/
├── data_download_workflow.md
├── 市水务局测站基本信息表/
├── 市水务局积涝水位数据/
└── 市水务局水库水位表/
```

- `download/data_download_workflow.md`：数据下载操作说明。
- `download/市水务局测站基本信息表/`：测站基础信息表下载结果。
- `download/市水务局积涝水位数据/`：积涝点水位数据，通常按月份归档。
- `download/市水务局水库水位表/`：水库水位数据，作为扩展数据源保留。

### `scripts/`

数据处理脚本目录。

```text
scripts/
├── download_flood_water_levels.py
├── import_water_levels_sqlite.py
└── check_local_database.py
```

- `download_flood_water_levels.py`：从深圳开放数据接口分页下载数据，保存原始 JSON 和 CSV。
- `import_water_levels_sqlite.py`：将下载后的 CSV 导入 SQLite。
- `check_local_database.py`：检查本地 SQLite 数据库中的表、记录和关联情况。

后续如果接入 FastAPI，可将这些能力逐步迁移或封装到 `backend/app/tasks/` 和 `backend/app/services/` 中。

### `tests/`

测试目录。

```text
tests/
├── test_download_flood_water_levels.py
└── test_import_water_levels_sqlite.py
```

- `test_download_flood_water_levels.py`：测试下载脚本的参数、字段映射和数据处理逻辑。
- `test_import_water_levels_sqlite.py`：测试 SQLite 导入逻辑。

后续新增后端和前端后，建议继续按模块增加测试文件。

## 2. 后续建议目录布局

当项目进入代码实现阶段，建议扩展为以下结构：

```text
.
├── backend/
├── frontend/
├── data/
├── docs/
├── download/
├── scripts/
├── tests/
├── task.md
└── PROJECT_STRUCTURE.md
```

### `backend/`

FastAPI 后端服务目录，负责接口、业务逻辑、数据库访问和任务调度。

```text
backend/
└── app/
    ├── main.py
    ├── core/
    ├── api/
    ├── models/
    ├── schemas/
    ├── services/
    ├── repositories/
    └── tasks/
```

- `app/main.py`：FastAPI 应用入口。
- `app/core/`：配置、数据库连接、定时任务等基础能力。
- `app/api/`：HTTP 路由，例如地图点位、统计、历史查询、坐标审核。
- `app/models/`：数据库模型。
- `app/schemas/`：接口输入输出结构。
- `app/services/`：业务逻辑，例如风险等级、趋势计算、地理编码。
- `app/repositories/`：数据库查询封装。
- `app/tasks/`：数据同步、导入和定时任务。

### `frontend/`

Vue 前端目录，负责指挥地图页面和后台管理页面。

```text
frontend/
└── src/
    ├── main.ts
    ├── router/
    ├── api/
    ├── map/
    ├── views/
    ├── components/
    └── stores/
```

- `src/main.ts`：前端入口。
- `src/router/`：页面路由。
- `src/api/`：封装后端接口请求。
- `src/map/`：地图适配层，例如 `MapProvider` 和 `AMapProvider`。
- `src/views/`：页面级组件，例如指挥地图、历史查询、点位校核、数据状态。
- `src/components/`：可复用组件，例如风险统计面板、点位弹窗、水位曲线。
- `src/stores/`：状态管理。

## 3. 核心文件职责约定

| 文件或目录 | 作用 |
|---|---|
| `task.md` | 原始需求入口 |
| `PROJECT_OVERVIEW.md` | 项目目标、主线流程和工程安排 |
| `PROJECT_STRUCTURE.md` | 项目目录和文件职责说明 |
| `docs/data_reference.md` | 数据源和字段说明 |
| `docs/superpowers/specs/` | 系统设计文档 |
| `docs/superpowers/plans/` | 项目计划和排期 |
| `download/` | 原始下载数据归档 |
| `data/local/` | 本地 SQLite 数据库 |
| `data/raw_samples/` | 样本页面或样本响应 |
| `scripts/` | 数据下载、导入、检查脚本 |
| `tests/` | 自动化测试 |
| `backend/` | 后端服务代码，后续新增 |
| `frontend/` | 前端页面代码，后续新增 |

## 4. 开发原则

1. 原始数据保留在 `download/`，不要只保留清洗后的结果。
2. 本地数据库放在 `data/local/`，不要混入脚本目录。
3. 数据源、字段和缺口统一记录到 `docs/data_reference.md`。
4. 系统设计和排期统一放到 `docs/superpowers/` 下。
5. 后端代码、前端代码和数据脚本保持目录边界清晰。
6. 当前优先打通实时水位接入、地图展示、统计查询、数据状态和轻量预测的主线闭环；告警、审计、工单、复杂机器学习训练和空间增强能力后续扩展。
