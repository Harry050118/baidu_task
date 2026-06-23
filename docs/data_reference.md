# 数据参考

本文档记录当前已经确认的数据源、字段映射、输出目录和已知缺口。下载操作说明见：

```text
download/data_download_workflow.md
```

## 数据源

| 数据集参数 | 数据源 | 接口 | 是否按时间查询 |
|---|---|---|---|
| `station` | 市水务局测站基本信息表 | `https://opendata.sz.gov.cn/api/1392394662/1/service.xhtml` | 否 |
| `flood` | 市水务局积涝点水位数据 | `https://opendata.sz.gov.cn/api/2920001403147/1/service.xhtml` | 是 |
| `reservoir` | 市水务局水库水位表 | `https://opendata.sz.gov.cn/api/1952552493/1/service.xhtml` | 是 |

统一下载脚本：

```bash
python3 scripts/download_flood_water_levels.py
```

## 输出目录

| 数据源 | 默认输出目录 |
|---|---|
| 测站基本信息表 | `download/市水务局测站基本信息表/` |
| 积涝点水位数据 | `download/市水务局积涝水位数据/YYYY-MM/` |
| 水库水位表 | `download/市水务局水库水位表/YYYY-MM/` |

每次下载会保存：

- CSV 汇总文件。
- `raw_pages/page_*.json` 原始分页响应。
- `download_metadata.json` 下载元数据。

## 字段映射

### 市水务局测站基本信息表

| CSV 字段 | API 字段 | 含义 |
|---|---|---|
| `测站编码` | `STCD` | 测站编码 |
| `测站名称` | `STNM` | 测站名称 |
| `站类` | `STTP` | 测站类型 |

已确认本次 API 下载：

| 指标 | 值 |
|---|---:|
| 记录数 | 485 |

### 市水务局积涝点水位数据

| CSV 字段 | API 字段 | 含义 |
|---|---|---|
| `测站编码` | `CZBM` | 测站编码，可关联测站基础信息 |
| `时间` | `SJ` | 观测时间 |
| `水位（m）` | `SW` | 水位，单位米 |
| `水位id` | `ID` | 原始水位记录 ID |

### 市水务局水库水位表

| CSV 字段 | API 字段 | 含义 |
|---|---|---|
| `测站编码` | `STCD` | 测站编码 |
| `自增ID` | `ID` | 原始记录 ID |
| `时水位（m）` | `RZ` | 时水位，单位米 |
| `采集时间` | `TM` | 水位采集时间 |

## SQLite 本地库

当前本地库路径：

```text
data/local/shenzhen_water.db
```

相关脚本：

```bash
python3 scripts/import_water_levels_sqlite.py --replace
python3 scripts/check_local_database.py
```

导入脚本会自动发现当前下载目录中的月度 CSV：

- `download/市水务局积涝水位数据/YYYY-MM/市水务局积涝点水位数据_2920001403147_YYYYMM.csv`
- `download/市水务局水库水位表/YYYY-MM/市水务局水库水位表_1952552493_YYYYMM.csv`
- `download/市水务局测站基本信息表/市水务局测站基本信息表_1392394662.csv`

最近一次完整导入结果：

| 表 | 行数 | 说明 |
|---|---:|---|
| `stations` | 485 | 测站基础信息 |
| `flood_water_levels` | 4,101,063 | 积涝点水位唯一记录 |
| `reservoir_water_levels` | 2,040,352 | 水库水位记录 |
| `source_imports` | 13 | 1 个测站文件、6 个积涝月度文件、6 个水库月度文件 |

积涝点 CSV 源文件合计处理 4,101,078 行，SQLite 表中为 4,101,063 行。差异来自 3 月文件内一个完全重复的 `水位id=599890334`，导入使用主键去重后保留 1 条唯一记录。

最近一次检查结果：

| 指标 | 值 |
|---|---:|
| 积涝点唯一测站编码 | 148 |
| 积涝点测站匹配基础信息 | 148 |
| 积涝点测站缺失基础信息 | 0 |
| 水库唯一测站编码 | 178 |
| 水库测站匹配基础信息 | 169 |
| 水库测站缺失基础信息 | 9 |
| 水库空/不可解析水位记录 | 40,982 |

## 已知缺口

### 缺少经纬度

当前已确认的测站基础信息表只有：

- `测站编码`
- `测站名称`
- `站类`

未发现：

- 经度
- 纬度
- 坐标
- 坐标系

因此地图落点暂时不能做，不能编造测站坐标。

### 水库测站编码匹配问题

早期本地库检查中，水库水位表有部分测站编码无法匹配到测站基础信息。后续如果继续使用 SQLite 或做关联分析，需要基于最新下载数据重新检查。

## 当前建议

1. 下载和更新数据时，优先使用 `scripts/download_flood_water_levels.py`。
2. 业务字段说明以本文档为准。
3. 操作步骤以 `download/data_download_workflow.md` 为准。
4. 做地图前，先补充可信的测站经纬度数据源。
