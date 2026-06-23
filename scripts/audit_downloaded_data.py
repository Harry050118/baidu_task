#!/usr/bin/env python3
"""Audit downloaded CSV files and the SQLite database."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = PROJECT_ROOT / "data" / "local" / "shenzhen_water.db"
DEFAULT_REPORT = PROJECT_ROOT / "docs" / "data_quality_report.md"


@dataclass
class NumericSummary:
    total: int = 0
    numeric_count: int = 0
    blank_count: int = 0
    dash_count: int = 0
    invalid_count: int = 0
    minimum: float | None = None
    maximum: float | None = None

    def add(self, value: str) -> None:
        self.total += 1
        stripped = value.strip()
        if stripped == "":
            self.blank_count += 1
            return
        if stripped == "-":
            self.dash_count += 1
            return
        try:
            number = float(stripped)
        except ValueError:
            self.invalid_count += 1
            return

        self.numeric_count += 1
        self.minimum = number if self.minimum is None else min(self.minimum, number)
        self.maximum = number if self.maximum is None else max(self.maximum, number)


@dataclass
class CsvAudit:
    dataset: str
    path: Path
    rows: int
    metadata_total: int | None
    metadata_rows_downloaded: int | None
    metadata_matches_csv: bool | None
    min_time: str | None = None
    max_time: str | None = None
    unique_ids: int | None = None
    duplicate_rows: int | None = None
    unique_stations: int | None = None
    numeric_summary: NumericSummary | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit downloaded water data.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite database")
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT,
        help="Markdown report output path",
    )
    return parser.parse_args()


def missing_dates(observed_dates: set[date], start: date, end: date) -> list[date]:
    current = start
    missing: list[date] = []
    while current <= end:
        if current not in observed_dates:
            missing.append(current)
        current += timedelta(days=1)
    return missing


def parse_observed_date(value: str) -> date | None:
    value = value.strip().lstrip("\ufeff").lstrip("\t").strip()
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").date()


def read_metadata(csv_path: Path) -> tuple[int | None, int | None]:
    metadata_path = csv_path.parent / "download_metadata.json"
    if not metadata_path.exists():
        return None, None
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    return metadata.get("total_reported_by_api"), metadata.get("rows_downloaded")


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return sum(1 for _ in csv.DictReader(file))


def audit_station_csv(path: Path) -> CsvAudit:
    total, downloaded = read_metadata(path)
    station_types: Counter[str] = Counter()
    station_codes: set[str] = set()
    duplicate_rows = 0

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = 0
        for row in reader:
            rows += 1
            code = row["测站编码"].strip()
            if code in station_codes:
                duplicate_rows += 1
            station_codes.add(code)
            station_types[row["站类"].strip()] += 1

    audit = CsvAudit(
        dataset="station",
        path=path,
        rows=rows,
        metadata_total=total,
        metadata_rows_downloaded=downloaded,
        metadata_matches_csv=(downloaded == rows if downloaded is not None else None),
        unique_ids=len(station_codes),
        duplicate_rows=duplicate_rows,
        unique_stations=len(station_codes),
    )
    audit.station_types = station_types  # type: ignore[attr-defined]
    return audit


def audit_water_csv(
    dataset: str,
    path: Path,
    id_field: str,
    station_field: str,
    time_field: str,
    level_field: str,
) -> CsvAudit:
    total, downloaded = read_metadata(path)
    ids: set[str] = set()
    duplicate_rows = 0
    stations: set[str] = set()
    numeric = NumericSummary()
    min_time: str | None = None
    max_time: str | None = None

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = 0
        for row in reader:
            rows += 1
            record_id = row[id_field].strip()
            if record_id in ids:
                duplicate_rows += 1
            ids.add(record_id)
            stations.add(row[station_field].strip())
            observed_at = row[time_field].strip().lstrip("\ufeff").lstrip("\t").strip()
            if observed_at:
                min_time = observed_at if min_time is None else min(min_time, observed_at)
                max_time = observed_at if max_time is None else max(max_time, observed_at)
            numeric.add(row[level_field])

    return CsvAudit(
        dataset=dataset,
        path=path,
        rows=rows,
        metadata_total=total,
        metadata_rows_downloaded=downloaded,
        metadata_matches_csv=(downloaded == rows if downloaded is not None else None),
        min_time=min_time,
        max_time=max_time,
        unique_ids=len(ids),
        duplicate_rows=duplicate_rows,
        unique_stations=len(stations),
        numeric_summary=numeric,
    )


def discover_downloaded_csvs() -> dict[str, list[Path]]:
    return {
        "station": sorted(
            (PROJECT_ROOT / "download" / "市水务局测站基本信息表").glob(
                "市水务局测站基本信息表_1392394662.csv"
            )
        ),
        "flood": sorted(
            (PROJECT_ROOT / "download" / "市水务局积涝水位数据").rglob(
                "市水务局积涝点水位数据_2920001403147_*.csv"
            )
        ),
        "reservoir": sorted(
            (PROJECT_ROOT / "download" / "市水务局水库水位表").rglob(
                "市水务局水库水位表_1952552493_*.csv"
            )
        ),
    }


def audit_csv_files() -> dict[str, list[CsvAudit]]:
    paths = discover_downloaded_csvs()
    return {
        "station": [audit_station_csv(path) for path in paths["station"]],
        "flood": [
            audit_water_csv(
                "flood",
                path,
                id_field="水位id",
                station_field="测站编码",
                time_field="时间",
                level_field="水位（m）",
            )
            for path in paths["flood"]
        ],
        "reservoir": [
            audit_water_csv(
                "reservoir",
                path,
                id_field="自增ID",
                station_field="测站编码",
                time_field="采集时间",
                level_field="时水位（m）",
            )
            for path in paths["reservoir"]
        ],
    }


def scalar(conn: sqlite3.Connection, sql: str) -> object:
    return conn.execute(sql).fetchone()[0]


def rows(conn: sqlite3.Connection, sql: str) -> list[sqlite3.Row]:
    return list(conn.execute(sql))


def sqlite_audit(db_path: Path) -> dict[str, object]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        result: dict[str, object] = {
            "tables": [
                row["name"]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                )
            ],
            "counts": {
                "stations": scalar(conn, "SELECT COUNT(*) FROM stations"),
                "flood_water_levels": scalar(conn, "SELECT COUNT(*) FROM flood_water_levels"),
                "reservoir_water_levels": scalar(
                    conn, "SELECT COUNT(*) FROM reservoir_water_levels"
                ),
                "source_imports": scalar(conn, "SELECT COUNT(*) FROM source_imports"),
            },
            "ranges": {
                "flood": (
                    scalar(conn, "SELECT MIN(observed_at) FROM flood_water_levels"),
                    scalar(conn, "SELECT MAX(observed_at) FROM flood_water_levels"),
                ),
                "reservoir": (
                    scalar(conn, "SELECT MIN(observed_at) FROM reservoir_water_levels"),
                    scalar(conn, "SELECT MAX(observed_at) FROM reservoir_water_levels"),
                ),
            },
            "station_matches": {
                "flood_matched": scalar(
                    conn,
                    """
                    SELECT COUNT(DISTINCT f.station_code)
                    FROM flood_water_levels AS f
                    INNER JOIN stations AS s ON s.station_code = f.station_code
                    """,
                ),
                "flood_missing": scalar(
                    conn,
                    """
                    SELECT COUNT(DISTINCT f.station_code)
                    FROM flood_water_levels AS f
                    LEFT JOIN stations AS s ON s.station_code = f.station_code
                    WHERE s.station_code IS NULL
                    """,
                ),
                "reservoir_matched": scalar(
                    conn,
                    """
                    SELECT COUNT(DISTINCT r.station_code)
                    FROM reservoir_water_levels AS r
                    INNER JOIN stations AS s ON s.station_code = r.station_code
                    """,
                ),
                "reservoir_missing": scalar(
                    conn,
                    """
                    SELECT COUNT(DISTINCT r.station_code)
                    FROM reservoir_water_levels AS r
                    LEFT JOIN stations AS s ON s.station_code = r.station_code
                    WHERE s.station_code IS NULL
                    """,
                ),
            },
            "reservoir_null_level": scalar(
                conn,
                "SELECT COUNT(*) FROM reservoir_water_levels WHERE water_level_m IS NULL",
            ),
            "station_types": rows(
                conn,
                """
                SELECT station_type, COUNT(*) AS count
                FROM stations
                GROUP BY station_type
                ORDER BY count DESC
                """,
            ),
            "reservoir_missing_station_codes": rows(
                conn,
                """
                SELECT r.station_code, COUNT(*) AS count
                FROM reservoir_water_levels AS r
                LEFT JOIN stations AS s ON s.station_code = r.station_code
                WHERE s.station_code IS NULL
                GROUP BY r.station_code
                ORDER BY count DESC, r.station_code
                """,
            ),
        }

        date_rows = rows(
            conn,
            """
            SELECT 'flood' AS dataset, substr(observed_at, 1, 10) AS day, COUNT(*) AS count
            FROM flood_water_levels
            GROUP BY day
            UNION ALL
            SELECT 'reservoir' AS dataset, substr(observed_at, 1, 10) AS day, COUNT(*) AS count
            FROM reservoir_water_levels
            GROUP BY day
            ORDER BY dataset, day
            """,
        )
        result["daily_counts"] = date_rows
        return result


def format_int(value: object) -> str:
    return f"{int(value):,}"


def markdown_table(headers: list[str], rows_: Iterable[Iterable[object]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("|" + "|".join("---" for _ in headers) + "|")
    for row in rows_:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return lines


def render_report(csv_audits: dict[str, list[CsvAudit]], db: dict[str, object]) -> str:
    lines: list[str] = [
        "# 已下载数据质量审计报告",
        "",
        f"- 生成时间: {datetime.now().isoformat(timespec='seconds')}",
        "- 范围: `download/` 中的 CSV、`download_metadata.json`、以及 `data/local/shenzhen_water.db`。",
        "",
        "## 总体结论",
        "",
    ]

    counts = db["counts"]  # type: ignore[assignment]
    lines.extend(
        [
            f"- 测站基础信息已导入 `{format_int(counts['stations'])}` 条。",
            f"- 积涝点水位 SQLite 唯一记录 `{format_int(counts['flood_water_levels'])}` 条。",
            f"- 水库水位 SQLite 记录 `{format_int(counts['reservoir_water_levels'])}` 条。",
            "- 积涝点 148 个测站编码全部能匹配测站基础信息。",
            "- 水库水位有 9 个测站编码暂未匹配测站基础信息。",
            "- 当前数据仍缺少经纬度字段，不能做准确地图落点。",
            "",
        ]
    )

    lines.append("## CSV 文件与元数据一致性")
    lines.append("")
    table_rows = []
    for dataset in ["station", "flood", "reservoir"]:
        for audit in csv_audits[dataset]:
            table_rows.append(
                [
                    dataset,
                    audit.path.parent.name,
                    audit.rows,
                    audit.metadata_rows_downloaded,
                    audit.metadata_total,
                    audit.metadata_matches_csv,
                    audit.duplicate_rows,
                    audit.unique_stations,
                ]
            )
    lines.extend(
        markdown_table(
            ["数据集", "目录", "CSV行数", "元数据rows", "元数据total", "是否一致", "重复ID行", "测站数"],
            table_rows,
        )
    )
    lines.append("")

    lines.append("## 时间范围与日期连续性")
    lines.append("")
    daily_counts = db["daily_counts"]  # type: ignore[assignment]
    by_dataset: dict[str, dict[date, int]] = defaultdict(dict)
    for row in daily_counts:
        by_dataset[row["dataset"]][datetime.strptime(row["day"], "%Y-%m-%d").date()] = row[
            "count"
        ]

    date_rows = []
    for dataset in ["flood", "reservoir"]:
        dates = set(by_dataset[dataset])
        start = min(dates)
        end = max(dates)
        gaps = missing_dates(dates, start, end)
        date_rows.append(
            [
                dataset,
                start,
                end,
                len(dates),
                len(gaps),
                ", ".join(str(item) for item in gaps[:20]) if gaps else "无",
            ]
        )
    lines.extend(
        markdown_table(["数据集", "最早日期", "最晚日期", "有数据日期数", "缺失日期数", "缺失日期示例"], date_rows)
    )
    lines.append("")
    lines.append(
        "说明：日期连续性按数据库中实际出现的 `observed_at` 日期检查。1 月数据包含 2025-12-31 的少量记录，属于接口按月份范围返回时的边界数据。"
    )
    lines.append("")

    lines.append("## 每日记录数概览")
    lines.append("")
    daily_rows = []
    for dataset in ["flood", "reservoir"]:
        values = list(by_dataset[dataset].values())
        min_day = min(by_dataset[dataset], key=lambda day: by_dataset[dataset][day])
        max_day = max(by_dataset[dataset], key=lambda day: by_dataset[dataset][day])
        daily_rows.append(
            [
                dataset,
                min(values),
                min_day,
                max(values),
                max_day,
                round(sum(values) / len(values), 2),
            ]
        )
    lines.extend(
        markdown_table(["数据集", "最少日记录数", "最少日期", "最多日记录数", "最多日期", "平均日记录数"], daily_rows)
    )
    lines.append("")

    lines.append("## 水位数值质量")
    lines.append("")
    numeric_rows = []
    for dataset in ["flood", "reservoir"]:
        total_numeric = NumericSummary()
        for audit in csv_audits[dataset]:
            summary = audit.numeric_summary
            if summary is None:
                continue
            total_numeric.total += summary.total
            total_numeric.numeric_count += summary.numeric_count
            total_numeric.blank_count += summary.blank_count
            total_numeric.dash_count += summary.dash_count
            total_numeric.invalid_count += summary.invalid_count
            if summary.minimum is not None:
                total_numeric.minimum = (
                    summary.minimum
                    if total_numeric.minimum is None
                    else min(total_numeric.minimum, summary.minimum)
                )
            if summary.maximum is not None:
                total_numeric.maximum = (
                    summary.maximum
                    if total_numeric.maximum is None
                    else max(total_numeric.maximum, summary.maximum)
                )
        numeric_rows.append(
            [
                dataset,
                total_numeric.total,
                total_numeric.numeric_count,
                total_numeric.blank_count,
                total_numeric.dash_count,
                total_numeric.invalid_count,
                total_numeric.minimum,
                total_numeric.maximum,
            ]
        )
    lines.extend(
        markdown_table(["数据集", "总行数", "可解析数值", "空白", "`-`", "非法值", "最小水位", "最大水位"], numeric_rows)
    )
    lines.append("")

    lines.append("## 测站关联情况")
    lines.append("")
    matches = db["station_matches"]  # type: ignore[assignment]
    lines.extend(
        markdown_table(
            ["项目", "数量"],
            [
                ["积涝测站匹配基础信息", matches["flood_matched"]],
                ["积涝测站缺失基础信息", matches["flood_missing"]],
                ["水库测站匹配基础信息", matches["reservoir_matched"]],
                ["水库测站缺失基础信息", matches["reservoir_missing"]],
            ],
        )
    )
    lines.append("")
    lines.append("### 水库未匹配测站编码")
    lines.append("")
    missing_rows = db["reservoir_missing_station_codes"]  # type: ignore[assignment]
    lines.extend(
        markdown_table(
            ["测站编码", "记录数"],
            [[row["station_code"], row["count"]] for row in missing_rows],
        )
    )
    lines.append("")

    lines.append("## 站类分布")
    lines.append("")
    station_types = db["station_types"]  # type: ignore[assignment]
    lines.extend(
        markdown_table(
            ["站类", "数量"],
            [[row["station_type"], row["count"]] for row in station_types],
        )
    )
    lines.append("")

    lines.append("## 主要问题清单")
    lines.append("")
    lines.extend(
        [
            "1. **缺少经纬度**：测站基础信息表没有坐标字段，地图落点暂时不能准确实现。",
            "2. **水库水位存在空水位**：水库 CSV 中共有 40,982 条空白水位，SQLite 中已写入 `NULL`，原始值保留在 `raw_water_level`。",
            "3. **水库测站有 9 个编码未匹配基础信息**：这些记录暂时无法补充测站名称和站类。",
            "4. **积涝 3 月文件存在重复 ID**：`水位id=599890334` 出现 16 次，内容完全相同；SQLite 主键去重后保留 1 条。",
            "5. **1 月数据含 2025-12-31 边界记录**：两个水位数据源的最早日期均为 2025-12-31，属于接口返回的月份边界数据，后续按月份统计时需要注意。",
            "",
        ]
    )

    lines.append("## 后续建议")
    lines.append("")
    lines.extend(
        [
            "1. 如果做页面或分析，优先使用 SQLite 表，避免直接扫大 CSV。",
            "2. 做月份统计时，用 `observed_at` 的真实日期分组，不要只依赖文件所在月份目录。",
            "3. 对水库水位分析时，显式排除 `water_level_m IS NULL`。",
            "4. 继续申请或寻找 `测站编码 + 经度 + 纬度 + 坐标系` 数据。",
        ]
    )

    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    csv_audits = audit_csv_files()
    db = sqlite_audit(args.db)
    report = render_report(csv_audits, db)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report, encoding="utf-8")
    print(f"Wrote {args.report}")


if __name__ == "__main__":
    main()
