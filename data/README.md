# SQLite 数据库说明

这份文档给第一次接触 SQLite 的人使用。它说明 `data/` 目录里有什么、数据库怎么写入、写入后有什么用，以及怎么把数据取出来。

## 1. data 目录里有什么

当前目录结构：

```text
data/
  local/
    shenzhen_water.db
  raw_samples/
    sample_station_page.html
    sample_water_level_page.html
```

重点文件是：

```text
data/local/shenzhen_water.db
```

它就是本项目的 SQLite 数据库文件。SQLite 的特点是：整个数据库就是一个普通文件，不需要单独启动数据库服务，也不需要账号、端口、密码。

## 2. SQLite 是什么

可以把 SQLite 理解成一个“放在本地文件里的 Excel 加强版”：

- CSV 适合保存单张表。
- SQLite 可以保存多张表。
- SQLite 可以用 SQL 查询、筛选、排序、关联多张表。
- SQLite 数据库只有一个 `.db` 文件，方便本地开发。

本项目现在把下载到的 CSV 数据导入 SQLite，是为了后续更方便地：

- 按测站编码查询数据。
- 查询某个测站的最新水位。
- 把水位数据和测站名称关联起来。
- 统计每个月、每个测站的数据量。
- 后续给页面、接口、图表或模型使用。

## 3. 数据从哪里写入数据库

数据库不是直接从 API 写入的，而是从已经下载好的 CSV 写入。

数据流程是：

```text
深圳开放数据 API
  -> download/ 下的 CSV 文件
  -> scripts/import_water_levels_sqlite.py
  -> data/local/shenzhen_water.db
```

也就是说：

1. 先用下载脚本把 API 数据下载成 CSV。
2. 再用导入脚本把 CSV 写进 SQLite。

## 4. 如何重新写入数据库

进入项目目录：

```bash
cd /Users/gjt/Documents/6.22
```

重新导入全部数据：

```bash
python3 scripts/import_water_levels_sqlite.py --replace
```

`--replace` 的意思是：

- 先清空数据库里旧的导入数据。
- 再把当前 `download/` 目录里的 CSV 重新导入。

如果你刚刚重新下载了 CSV，建议使用 `--replace`，这样数据库内容会和当前 CSV 保持一致。

## 5. 导入脚本会读取哪些文件

导入脚本会自动寻找这些文件：

### 测站基本信息表

```text
download/市水务局测站基本信息表/市水务局测站基本信息表_1392394662.csv
```

### 积涝点水位数据

```text
download/市水务局积涝水位数据/YYYY-MM/市水务局积涝点水位数据_2920001403147_YYYYMM.csv
```

例如：

```text
download/市水务局积涝水位数据/2026-01/市水务局积涝点水位数据_2920001403147_202601.csv
```

### 水库水位表

```text
download/市水务局水库水位表/YYYY-MM/市水务局水库水位表_1952552493_YYYYMM.csv
```

例如：

```text
download/市水务局水库水位表/2026-01/市水务局水库水位表_1952552493_202601.csv
```

## 6. 当前数据库里有哪些表

当前数据库有 4 张主要表。

### stations

测站基础信息。

| 字段 | 含义 |
|---|---|
| `station_code` | 测站编码，主键 |
| `station_name` | 测站名称 |
| `station_type` | 站类，例如内涝水情站、水库水位站 |
| `source_file` | 来源 CSV |
| `imported_at` | 导入时间 |

### flood_water_levels

积涝点水位数据。

| 字段 | 含义 |
|---|---|
| `id` | 水位记录 ID，主键 |
| `station_code` | 测站编码 |
| `observed_at` | 观测时间 |
| `water_level_m` | 数字水位，单位米 |
| `raw_water_level` | 原始水位文本 |
| `source_file` | 来源 CSV |
| `imported_at` | 导入时间 |

### reservoir_water_levels

水库水位数据。

| 字段 | 含义 |
|---|---|
| `id` | 水位记录 ID，主键 |
| `station_code` | 测站编码 |
| `observed_at` | 采集时间 |
| `water_level_m` | 数字水位，单位米；空值会写成 `NULL` |
| `raw_water_level` | 原始水位文本 |
| `source_file` | 来源 CSV |
| `imported_at` | 导入时间 |

### source_imports

每次导入的来源记录。

| 字段 | 含义 |
|---|---|
| `source_file` | 导入的 CSV 文件 |
| `source_format` | 文件格式，目前是 `csv` |
| `imported_at` | 导入时间 |
| `row_count` | 该文件处理了多少行 |

## 7. 当前导入结果

最近一次完整导入结果：

| 表 | 行数 |
|---|---:|
| `stations` | 485 |
| `flood_water_levels` | 4,101,063 |
| `reservoir_water_levels` | 2,040,352 |
| `source_imports` | 13 |

说明：

- 积涝点 CSV 源文件一共处理了 4,101,078 行。
- SQLite 表里是 4,101,063 行。
- 差异来自 3 月文件里一个完全重复的 `水位id=599890334`，数据库用主键去重后只保留 1 条。
- 水库水位中有 40,982 条空水位，数据库里 `water_level_m` 写成 `NULL`，原始文本仍保存在 `raw_water_level`。

## 8. 如何检查数据库是否正常

运行：

```bash
python3 scripts/check_local_database.py
```

它会输出：

- 数据库里有哪些表。
- 每张水位表有多少行。
- 时间范围。
- 有多少测站能匹配到基础信息表。
- 抽样数据。
- 每个 CSV 文件导入了多少行。

## 9. 如何直接查询数据库

macOS 通常自带 `sqlite3` 命令。可以这样打开数据库：

```bash
sqlite3 data/local/shenzhen_water.db
```

进入后，可以输入 SQL。

显示所有表：

```sql
.tables
```

查看表结构：

```sql
.schema stations
.schema flood_water_levels
.schema reservoir_water_levels
```

退出 SQLite：

```sql
.quit
```

## 10. 常用查询示例

### 查看测站数量

```sql
SELECT COUNT(*) FROM stations;
```

### 查看不同站类有多少个

```sql
SELECT station_type, COUNT(*) AS count
FROM stations
GROUP BY station_type
ORDER BY count DESC;
```

### 查看最新 10 条积涝点水位

```sql
SELECT *
FROM flood_water_levels
ORDER BY observed_at DESC
LIMIT 10;
```

### 查看某个测站的积涝点水位历史

把 `9281192020` 换成你想看的测站编码：

```sql
SELECT observed_at, water_level_m
FROM flood_water_levels
WHERE station_code = '9281192020'
ORDER BY observed_at;
```

### 查询每个积涝测站的最新水位

```sql
SELECT
    f.station_code,
    s.station_name,
    s.station_type,
    f.observed_at,
    f.water_level_m
FROM flood_water_levels AS f
LEFT JOIN stations AS s
    ON s.station_code = f.station_code
INNER JOIN (
    SELECT station_code, MAX(observed_at) AS latest_time
    FROM flood_water_levels
    GROUP BY station_code
) AS latest
    ON latest.station_code = f.station_code
   AND latest.latest_time = f.observed_at
ORDER BY f.water_level_m DESC;
```

### 查询水位最高的 20 条积涝记录

```sql
SELECT
    f.station_code,
    s.station_name,
    f.observed_at,
    f.water_level_m
FROM flood_water_levels AS f
LEFT JOIN stations AS s
    ON s.station_code = f.station_code
ORDER BY f.water_level_m DESC
LIMIT 20;
```

### 查看水库水位空值数量

```sql
SELECT COUNT(*)
FROM reservoir_water_levels
WHERE water_level_m IS NULL;
```

### 查看每个 CSV 文件导入了多少行

```sql
SELECT source_file, row_count
FROM source_imports
ORDER BY source_file;
```

## 11. 如何在 Python 里取数据

可以用 Python 标准库 `sqlite3`，不需要安装额外依赖。

示例：读取最新 5 条积涝点水位：

```python
import sqlite3

db_path = "data/local/shenzhen_water.db"

with sqlite3.connect(db_path) as conn:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT
            f.station_code,
            s.station_name,
            f.observed_at,
            f.water_level_m
        FROM flood_water_levels AS f
        LEFT JOIN stations AS s
            ON s.station_code = f.station_code
        ORDER BY f.observed_at DESC
        LIMIT 5
        """
    ).fetchall()

for row in rows:
    print(dict(row))
```

## 12. 这个数据库后续有什么用

后续可以基于 SQLite 做这些事：

- 给后端接口提供查询数据。
- 给前端页面提供表格数据。
- 查询某个测站的历史曲线。
- 查询最新水位。
- 做数据质量检查。
- 后续在拿到经纬度后，把测站编码关联到地图点位。

现在经纬度暂时没有，不影响先做数据库、表格、曲线和统计。

## 13. 注意事项

- 不要手动编辑 `.db` 文件本身。
- 需要更新数据库时，重新运行导入脚本。
- `--replace` 会清空旧导入结果，再重新写入。
- 如果 CSV 被重新下载，建议重新导入数据库。
- 如果查询很慢，可以后续再增加索引；当前已经对水位表的 `station_code` 和 `observed_at` 建了常用索引。
