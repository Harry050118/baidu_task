# 深圳市积水监测与预测系统调用链图

本文档用一张可直接渲染、可编辑的 Mermaid 调用链图说明深圳市积水监测与预测系统的主流程。系统先打通“实时水位接入、数据治理、坐标补全、接口服务、地图展示”的监测闭环；初期基于人工规则做风险研判和趋势提示；后期在历史数据沉淀基础上训练模型，并接入模型预测服务。

```mermaid
%%{init: {
  "theme": "dark",
  "themeVariables": {
    "fontSize": "22px",
    "actorFontSize": "22px",
    "messageFontSize": "21px",
    "noteFontSize": "20px",
    "actorBorder": "#2f8fbd",
    "actorBkg": "#20262e",
    "actorTextColor": "#f3f7fb",
    "signalColor": "#e6eef8",
    "signalTextColor": "#f3f7fb",
    "noteBkgColor": "#20262e",
    "noteTextColor": "#f3f7fb",
    "noteBorderColor": "#2f8fbd"
  }
}}%%
sequenceDiagram
    autonumber
    participant OpenData as 深圳开放数据
    participant Ingest as 实时采集任务
    participant Archive as 原始归档
    participant SQLite as SQLite 数据库
    participant Coord as 坐标补全服务
    participant Service as 数据治理服务
    participant Predict as 研判/预测服务
    participant Train as 模型训练
    participant API as FastAPI 接口
    participant Web as Vue + 高德地图

    OpenData->>Ingest: 实时/定时拉取水位数据、测站信息
    Ingest->>Archive: 保存原始 JSON、CSV、下载元数据
    Ingest->>SQLite: 增量入库测站、水位、导入批次
    Ingest->>Coord: 提供测站名称、地址、测站编码
    Coord->>Coord: 调用高德 API 生成初步经纬度<br/>标记来源=高德、精度=待校核
    Coord->>SQLite: 写入临时坐标、候选列表、坐标来源
    SQLite->>Service: 提供最新水位、历史水位、测站信息

    Service->>Service: 数据治理<br/>空值、重复、时间口径、数据新鲜度
    Service->>Service: 计算实时风险与趋势<br/>正常、关注、警戒、危险

    API->>Service: 查询地图点位、实时风险、历史曲线、数据状态
    Service-->>API: 返回最新水位、趋势、统计、导入状态
    API-->>Web: 输出地图点位、风险颜色、统计面板、历史曲线
    Web->>Web: 展示监测闭环<br/>点位、风险颜色、行政区边界、点位弹窗

    Note over OpenData,Web: 第一阶段主链路：实时数据接入 → 原始归档 → SQLite 入库 → 数据治理 → API 输出 → 地图展示

    opt 初期研判闭环：规则趋势提示
        API->>Predict: 请求风险研判
        Predict->>SQLite: 读取最近有效水位序列
        Predict->>Predict: 规则研判<br/>基于当前水位、趋势、数据新鲜度
        Predict-->>API: 返回风险等级、趋势提示、规则说明
        API->>SQLite: 回写研判结果
        API-->>Web: 展示风险等级和趋势提示
    end

    opt 后期模型升级：训练模型并接入服务
        SQLite->>Train: 抽取历史样本、预测标签、临时坐标
        Train->>Train: 特征工程<br/>近实时水位序列、每秒水位变化、降水量、时间特征、站点特征、空间特征
        Train->>Train: 使用高德初步坐标训练<br/>保留坐标来源和精度标记
        Train->>Train: 6 月滚动测试<br/>按小雨、中雨、暴雨统计准确率
        Train->>Train: 训练、评估、保存模型版本
        Train-->>Predict: 发布可用模型
        Predict->>Predict: 使用模型输出短时积水预测
        Predict-->>API: 返回预测风险、预测趋势、置信度
        Predict-->>SQLite: 记录模型版本、评估指标、训练时间
    end

    opt 坐标校核与标准数据替换
        Web->>API: 提交点位名称或地址
        API->>Coord: 生成或查询高德候选坐标
        Coord-->>Web: 返回候选坐标和来源标记
        Web->>API: 人工审核通过坐标
        API->>SQLite: 写入审核后的地图坐标
        Coord->>SQLite: 政府标准坐标到位后替换或校正
        SQLite->>Train: 坐标更新后触发样本修正和模型重训
    end
```

## 流程说明

1. 第一阶段先打通监测闭环：开放数据接入、原始归档、SQLite 入库、坐标补全、数据治理、FastAPI 接口、Vue + 高德地图展示。
2. 第二阶段加入规则研判：基于当前水位、最近趋势和数据新鲜度生成风险等级、趋势提示和规则说明，并把研判结果回写数据库和前端页面。
3. 坐标数据分两步处理：先申请高德 API 获取初步经纬度并标记为临时坐标，同时申请政府标准坐标；标准坐标到位后用于校正、替换和重新训练模型。
4. 第三阶段升级模型预测：当历史水位、临时坐标和扩展数据沉淀足够后，再构建训练样本、训练模型、评估模型并发布到研判/预测服务。模型评估采用 6 月滚动测试，按预测日之前的数据训练、预测日及之后的数据测试。
5. 研判/预测服务是系统的统一风险输出口，初期由规则研判驱动，后期由训练模型增强预测能力。
6. 地图展示和模型训练都必须保留坐标来源、坐标精度和审核状态，避免把高德初步坐标当作政府标准坐标使用。

## 图中关键模块

| 模块 | 说明 |
|---|---|
| 深圳开放数据 | 积涝水位数据、测站基础信息，后续可扩展降水量、道路、历史易涝点 |
| 实时采集任务 | 实时或定时拉取数据，完成增量同步、失败重试和导入批次记录 |
| 原始归档 | 保存 JSON、CSV 和下载元数据，保证数据可追溯 |
| SQLite 数据库 | 保存测站、水位、导入批次、临时坐标、标准坐标、审核状态、历史样本、研判结果和预测结果 |
| 坐标补全服务 | 使用高德 API 获取初步经纬度，记录坐标来源和精度；政府标准坐标到位后校正或替换 |
| 数据治理服务 | 数据质量检查、时间口径处理、实时风险等级和趋势计算 |
| 研判/预测服务 | 初期执行规则研判和趋势提示，后期接入训练后的模型进行短时积水风险预测 |
| 模型训练 | 历史样本抽取、降水特征接入、坐标特征处理、特征工程、6 月滚动测试、分雨强评估和版本发布 |
| FastAPI 接口 | 实时水位、历史曲线、研判/预测结果、导入状态和坐标校核 |
| Vue + 高德地图 | 展示实时积水态势、趋势提示、预测趋势、风险等级、历史曲线和点位弹窗 |

## 后续落地目录

```text
.
├── backend/
│   └── app/
│       ├── main.py
│       ├── core/
│       ├── api/
│       ├── models/
│       ├── schemas/
│       ├── services/
│       ├── repositories/
│       └── tasks/
├── frontend/
│   └── src/
│       ├── main.ts
│       ├── router/
│       ├── api/
│       ├── map/
│       ├── views/
│       ├── components/
│       └── stores/
├── data/
├── docs/
├── download/
├── scripts/
└── tests/
```

## 开发边界

1. 当前主线优先打通实时水位接入、SQLite 入库、数据治理、FastAPI 接口和 Vue 地图展示。
2. 原始数据必须保留在 `download/`，清洗和导入结果不能替代原始归档。
3. 当前没有测站经纬度时，可以先用高德 API 生成初步坐标，但必须记录 `coord_source=amap`、精度状态和审核状态。
4. 高德初步坐标可以进入初期训练样本，但不能等同于政府标准坐标；政府标准坐标到位后需要校正样本并重新训练或评估模型。
5. 降水量尚未获取时先运行无降水基线；降水量到位后必须接入增强模型，并对小雨、中雨、暴雨场景分别统计预测准确率。
6. 地图点位对外展示应区分临时坐标、人工审核坐标和政府标准坐标，不能为了演示随意编造经纬度。
7. 初期不称为模型预测，只做规则研判和趋势提示；历史样本足够后再训练机器学习模型。
8. 告警、审计、工单、权限和 PostGIS 迁移属于后续扩展，不阻塞当前监测与预测闭环。
