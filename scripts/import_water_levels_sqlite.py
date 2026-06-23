#!/usr/bin/env python3
"""Import downloaded water data CSV files into a local SQLite database."""

from __future__ import annotations

import argparse
import csv
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = (
    PROJECT_ROOT
    / "download"
    / "市水务局水库水位表"
    / "市水务局水库水位表_1952552493.csv"
)
DEFAULT_RESERVOIR_DIR = PROJECT_ROOT / "download" / "市水务局水库水位表"
DEFAULT_STATIONS_CSV = (
    PROJECT_ROOT
    / "download"
    / "市水务局测站基本信息表"
    / "市水务局测站基本信息表_1392394662.csv"
)
DEFAULT_FLOOD_DIR = PROJECT_ROOT / "download" / "市水务局积涝水位数据"
DEFAULT_FLOOD_CSV = (
    PROJECT_ROOT
    / "download"
    / "市水务局积涝水位数据"
    / "市水务局积涝点水位数据_2920001403147.csv"
)
DEFAULT_DB = PROJECT_ROOT / "data" / "local" / "shenzhen_water.db"
RESERVOIR_CSV_PATTERN = "市水务局水库水位表_1952552493_*.csv"
FLOOD_CSV_PATTERN = "市水务局积涝点水位数据_2920001403147_*.csv"

WATER_LEVEL_FIELDS = ["测站编码", "自增ID", "时水位（m）", "采集时间"]
STATION_FIELDS = ["测站编码", "测站名称", "站类"]
FLOOD_WATER_LEVEL_FIELDS = ["测站编码", "时间", "水位（m）", "水位id"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import downloaded station and water-level CSV rows into SQLite."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        action="append",
        default=None,
        help="Reservoir CSV file to import. Can be used multiple times.",
    )
    parser.add_argument(
        "--reservoir-dir",
        type=Path,
        default=DEFAULT_RESERVOIR_DIR,
        help="Directory containing monthly reservoir CSV files",
    )
    parser.add_argument(
        "--stations-csv",
        type=Path,
        default=DEFAULT_STATIONS_CSV,
        help="Station basic information CSV file to import",
    )
    parser.add_argument(
        "--flood-csv",
        type=Path,
        action="append",
        default=None,
        help="Flooding-point water-level CSV file to import. Can be used multiple times.",
    )
    parser.add_argument(
        "--flood-dir",
        type=Path,
        default=DEFAULT_FLOOD_DIR,
        help="Directory containing monthly flooding-point CSV files",
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite database path")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Clear existing imported rows before importing this CSV",
    )
    return parser.parse_args()


def discover_csv_files(base_dir: Path, pattern: str) -> list[Path]:
    if not base_dir.exists():
        return []
    return sorted(path for path in base_dir.rglob(pattern) if path.is_file())


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS source_imports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_file TEXT NOT NULL,
            source_format TEXT NOT NULL,
            imported_at TEXT NOT NULL,
            row_count INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS stations (
            station_code TEXT PRIMARY KEY,
            station_name TEXT NOT NULL,
            station_type TEXT NOT NULL,
            source_file TEXT NOT NULL,
            imported_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS reservoir_water_levels (
            id TEXT PRIMARY KEY,
            station_code TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            water_level_m REAL,
            raw_water_level TEXT NOT NULL,
            source_file TEXT NOT NULL,
            imported_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_reservoir_water_levels_station_time
            ON reservoir_water_levels (station_code, observed_at);

        CREATE INDEX IF NOT EXISTS idx_reservoir_water_levels_observed_at
            ON reservoir_water_levels (observed_at);

        CREATE TABLE IF NOT EXISTS flood_water_levels (
            id TEXT PRIMARY KEY,
            station_code TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            water_level_m REAL NOT NULL,
            raw_water_level TEXT NOT NULL,
            source_file TEXT NOT NULL,
            imported_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_flood_water_levels_station_time
            ON flood_water_levels (station_code, observed_at);

        CREATE INDEX IF NOT EXISTS idx_flood_water_levels_observed_at
            ON flood_water_levels (observed_at);
        """
    )


def clean_time(value: str) -> str:
    return value.strip().lstrip("\ufeff").lstrip("\t").strip()


def parse_water_level(value: str) -> float | None:
    value = value.strip()
    if value in {"", "-"}:
        return None
    return float(value)


def validate_header(fieldnames: list[str] | None, expected_fields: list[str]) -> None:
    if fieldnames != expected_fields:
        raise ValueError(
            f"Unexpected CSV fields: {fieldnames!r}. Expected: {expected_fields!r}"
        )


def relative_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)


def import_stations(
    conn: sqlite3.Connection, stations_csv_path: Path, imported_at: str
) -> int:
    if not stations_csv_path.exists():
        return 0

    row_count = 0
    with stations_csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        validate_header(reader.fieldnames, STATION_FIELDS)
        for row in reader:
            conn.execute(
                """
                INSERT OR REPLACE INTO stations (
                    station_code,
                    station_name,
                    station_type,
                    source_file,
                    imported_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    row["测站编码"].strip(),
                    row["测站名称"].strip(),
                    row["站类"].strip(),
                    relative_path(stations_csv_path),
                    imported_at,
                ),
            )
            row_count += 1

    conn.execute(
        """
        INSERT INTO source_imports (
            source_file,
            source_format,
            imported_at,
            row_count
        ) VALUES (?, ?, ?, ?)
        """,
        (relative_path(stations_csv_path), "csv", imported_at, row_count),
    )
    return row_count


def import_water_levels(
    conn: sqlite3.Connection, csv_path: Path, imported_at: str
) -> int:
    if not csv_path.exists():
        return 0

    row_count = 0
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        validate_header(reader.fieldnames, WATER_LEVEL_FIELDS)
        for row in reader:
            raw_level = row["时水位（m）"].strip()
            conn.execute(
                """
                INSERT OR REPLACE INTO reservoir_water_levels (
                    id,
                    station_code,
                    observed_at,
                    water_level_m,
                    raw_water_level,
                    source_file,
                    imported_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["自增ID"].strip(),
                    row["测站编码"].strip(),
                    clean_time(row["采集时间"]),
                    parse_water_level(raw_level),
                    raw_level,
                    relative_path(csv_path),
                    imported_at,
                ),
            )
            row_count += 1

    conn.execute(
        """
        INSERT INTO source_imports (
            source_file,
            source_format,
            imported_at,
            row_count
        ) VALUES (?, ?, ?, ?)
        """,
        (relative_path(csv_path), "csv", imported_at, row_count),
    )

    return row_count


def import_flood_water_levels(
    conn: sqlite3.Connection, flood_csv_path: Path, imported_at: str
) -> int:
    if not flood_csv_path.exists():
        return 0

    row_count = 0
    with flood_csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        validate_header(reader.fieldnames, FLOOD_WATER_LEVEL_FIELDS)
        for row in reader:
            raw_level = row["水位（m）"].strip()
            conn.execute(
                """
                INSERT OR REPLACE INTO flood_water_levels (
                    id,
                    station_code,
                    observed_at,
                    water_level_m,
                    raw_water_level,
                    source_file,
                    imported_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["水位id"].strip(),
                    row["测站编码"].strip(),
                    clean_time(row["时间"]),
                    float(raw_level),
                    raw_level,
                    relative_path(flood_csv_path),
                    imported_at,
                ),
            )
            row_count += 1

    conn.execute(
        """
        INSERT INTO source_imports (
            source_file,
            source_format,
            imported_at,
            row_count
        ) VALUES (?, ?, ?, ?)
        """,
        (relative_path(flood_csv_path), "csv", imported_at, row_count),
    )
    return row_count


def import_csv(
    reservoir_csv_paths: list[Path],
    stations_csv_path: Path,
    flood_csv_paths: list[Path],
    db_path: Path,
    replace: bool,
) -> tuple[int, int, int]:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    imported_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with sqlite3.connect(db_path) as conn:
        create_schema(conn)
        if replace:
            conn.execute("DELETE FROM reservoir_water_levels")
            conn.execute("DELETE FROM flood_water_levels")
            conn.execute("DELETE FROM stations")
            conn.execute("DELETE FROM source_imports")

        station_count = import_stations(conn, stations_csv_path, imported_at)
        flood_water_level_count = sum(
            import_flood_water_levels(conn, flood_csv_path, imported_at)
            for flood_csv_path in flood_csv_paths
        )
        water_level_count = sum(
            import_water_levels(conn, csv_path, imported_at)
            for csv_path in reservoir_csv_paths
        )

    return station_count, flood_water_level_count, water_level_count


def selected_reservoir_csvs(args: argparse.Namespace) -> list[Path]:
    if args.csv:
        return args.csv
    discovered = discover_csv_files(args.reservoir_dir, RESERVOIR_CSV_PATTERN)
    if discovered:
        return discovered
    if DEFAULT_CSV.exists():
        return [DEFAULT_CSV]
    return []


def selected_flood_csvs(args: argparse.Namespace) -> list[Path]:
    if args.flood_csv:
        return args.flood_csv
    discovered = discover_csv_files(args.flood_dir, FLOOD_CSV_PATTERN)
    if discovered:
        return discovered
    if DEFAULT_FLOOD_CSV.exists():
        return [DEFAULT_FLOOD_CSV]
    return []


def main() -> None:
    args = parse_args()
    reservoir_csv_paths = selected_reservoir_csvs(args)
    flood_csv_paths = selected_flood_csvs(args)
    station_count, flood_water_level_count, water_level_count = import_csv(
        reservoir_csv_paths,
        args.stations_csv,
        flood_csv_paths,
        args.db,
        args.replace,
    )
    print(f"Imported {station_count} station rows into {args.db}")
    print(f"Imported {flood_water_level_count} flood water-level rows into {args.db}")
    print(f"Imported {water_level_count} water-level rows into {args.db}")


if __name__ == "__main__":
    main()
