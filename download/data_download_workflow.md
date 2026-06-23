# 水位数据下载工作流

## 1. 准备 appKey

项目根目录需要有 `.env` 文件：

```text
/Users/gjt/Documents/6.22/.env
```

文件内容格式如下：

```text
APP_KEY=你的真实appKey
```

不要把真实 appKey 写进文档、截图或聊天记录。

## 2. 进入项目目录

```bash
cd /Users/gjt/Documents/6.22
```

## 3. 可下载的数据源

| 参数 | 数据源 | 接口 |
|---|---|---|
| `--dataset station` | 市水务局测站基本信息表 | `https://opendata.sz.gov.cn/api/1392394662/1/service.xhtml` |
| `--dataset flood` | 市水务局积涝点水位数据 | `https://opendata.sz.gov.cn/api/2920001403147/1/service.xhtml` |
| `--dataset reservoir` | 市水务局水库水位表 | `https://opendata.sz.gov.cn/api/1952552493/1/service.xhtml` |

## 4. 下载测站基本信息表

测站基本信息表不需要时间参数：

```bash
python3 scripts/download_flood_water_levels.py --dataset station --rows 10000 --sleep 0.05
```

输出目录：

```text
download/市水务局测站基本信息表/
```

输出文件：

```text
市水务局测站基本信息表_1392394662.csv
raw_pages/page_00001.json
download_metadata.json
```

注意：`station` 不支持 `--months`，因为测站基础信息不是按月份变化的水位数据。

## 5. 下载水库水位表

下载 2026 年 1 月到 6 月：

```bash
python3 scripts/download_flood_water_levels.py --dataset reservoir --months 202601 202602 202603 202604 202605 202606 --rows 10000 --sleep 0.05
```

输出目录：

```text
download/市水务局水库水位表/2026-01/
download/市水务局水库水位表/2026-02/
download/市水务局水库水位表/2026-03/
download/市水务局水库水位表/2026-04/
download/市水务局水库水位表/2026-05/
download/市水务局水库水位表/2026-06/
```

## 6. 下载积涝点水位数据

下载 2026 年 1 月到 6 月：

```bash
python3 scripts/download_flood_water_levels.py --dataset flood --months 202601 202602 202603 202604 202605 202606 --rows 10000 --sleep 0.05
```

输出目录：

```text
download/市水务局积涝水位数据/2026-01/
download/市水务局积涝水位数据/2026-02/
download/市水务局积涝水位数据/2026-03/
download/市水务局积涝水位数据/2026-04/
download/市水务局积涝水位数据/2026-05/
download/市水务局积涝水位数据/2026-06/
```

## 7. 手动指定日期范围

如果不想按整月下载，可以手动指定开始和结束日期。

```bash
python3 scripts/download_flood_water_levels.py --dataset reservoir --start-date 20260601 --end-date 20260623 --rows 10000 --sleep 0.05 --output-dir "download/市水务局水库水位表/2026-06" --csv "download/市水务局水库水位表/2026-06/市水务局水库水位表_1952552493_202606.csv"
```

## 8. 检查下载结果

查看 CSV 行数：

```bash
wc -l "download/市水务局测站基本信息表/市水务局测站基本信息表_1392394662.csv"
```

注意：`wc -l` 的结果包含表头，所以数据条数通常是输出行数减 1。

查看元数据：

```bash
cat "download/市水务局测站基本信息表/download_metadata.json"
```

重点看：

```text
rows_downloaded
total_reported_by_api
```

这两个值一致时，说明本次分页下载完整。

## 9. 常见问题

如果看到 `Missing appKey`，说明 `.env` 文件不存在，或里面没有 `APP_KEY=...`。

如果看到 `API error 10001: 未经许可的证书`，说明 appKey 可能没有订阅该接口，或 appKey 复制错了。

重复运行同一个下载命令会覆盖同一个输出目录下的同名 CSV 和 `raw_pages/page_*.json`。
