#!/usr/bin/env python3
"""
Print a small health report for the local SQLite water database.
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = PROJECT_ROOT / "data" / "local" / "shenzhen_water.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the local SQLite database.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite database path")
    return parser.parse_args()


def scalar(conn: sqlite3.Connection, sql: str) -> object:
    return conn.execute(sql).fetchone()[0]


def main() -> None:
    args = parse_args()
    if not args.db.exists():
        raise FileNotFoundError(f"Database not found: {args.db}")

    with sqlite3.connect(args.db) as conn:
        conn.row_factory = sqlite3.Row

        print(f"Database: {args.db}")
        print("Tables:")
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ):
            print(f"- {row['name']}")

        print("\nreservoir_water_levels:")
        print(f"- rows: {scalar(conn, 'SELECT COUNT(*) FROM reservoir_water_levels')}")
        print(
            "- unique station_code: "
            f"{scalar(conn, 'SELECT COUNT(DISTINCT station_code) FROM reservoir_water_levels')}"
        )
        print(
            "- observed_at range: "
            f"{scalar(conn, 'SELECT MIN(observed_at) FROM reservoir_water_levels')}"
            " to "
            f"{scalar(conn, 'SELECT MAX(observed_at) FROM reservoir_water_levels')}"
        )
        print(
            "- numeric water_level_m rows: "
            f"{scalar(conn, 'SELECT COUNT(*) FROM reservoir_water_levels WHERE water_level_m IS NOT NULL')}"
        )
        print(
            "- missing/non-numeric water_level_m rows: "
            f"{scalar(conn, 'SELECT COUNT(*) FROM reservoir_water_levels WHERE water_level_m IS NULL')}"
        )

        print("\nstations:")
        print(f"- rows: {scalar(conn, 'SELECT COUNT(*) FROM stations')}")
        print(
            "- station types: "
            f"{scalar(conn, 'SELECT COUNT(DISTINCT station_type) FROM stations')}"
        )
        print("- longitude/latitude fields: not present in confirmed source data")
        reservoir_matched_count = scalar(
            conn,
            """
            SELECT COUNT(DISTINCT w.station_code)
            FROM reservoir_water_levels AS w
            INNER JOIN stations AS s
                ON s.station_code = w.station_code
            """,
        )
        reservoir_missing_count = scalar(
            conn,
            """
            SELECT COUNT(DISTINCT w.station_code)
            FROM reservoir_water_levels AS w
            LEFT JOIN stations AS s
                ON s.station_code = w.station_code
            WHERE s.station_code IS NULL
            """,
        )
        print(
            "- water-level station codes matched in stations: "
            f"{reservoir_matched_count}"
        )
        print(
            "- water-level station codes missing from stations: "
            f"{reservoir_missing_count}"
        )

        print("\nflood_water_levels:")
        print(f"- rows: {scalar(conn, 'SELECT COUNT(*) FROM flood_water_levels')}")
        print(
            "- unique station_code: "
            f"{scalar(conn, 'SELECT COUNT(DISTINCT station_code) FROM flood_water_levels')}"
        )
        print(
            "- observed_at range: "
            f"{scalar(conn, 'SELECT MIN(observed_at) FROM flood_water_levels')}"
            " to "
            f"{scalar(conn, 'SELECT MAX(observed_at) FROM flood_water_levels')}"
        )
        flood_matched_count = scalar(
            conn,
            """
            SELECT COUNT(DISTINCT f.station_code)
            FROM flood_water_levels AS f
            INNER JOIN stations AS s
                ON s.station_code = f.station_code
            """,
        )
        flood_missing_count = scalar(
            conn,
            """
            SELECT COUNT(DISTINCT f.station_code)
            FROM flood_water_levels AS f
            LEFT JOIN stations AS s
                ON s.station_code = f.station_code
            WHERE s.station_code IS NULL
            """,
        )
        print(
            "- station codes matched in stations: "
            f"{flood_matched_count}"
        )
        print(
            "- station codes missing from stations: "
            f"{flood_missing_count}"
        )

        print("\nSample rows:")
        for row in conn.execute(
            """
            SELECT
                w.id,
                w.station_code,
                s.station_name,
                s.station_type,
                w.observed_at,
                w.water_level_m,
                w.raw_water_level
            FROM reservoir_water_levels AS w
            LEFT JOIN stations AS s
                ON s.station_code = w.station_code
            ORDER BY w.observed_at DESC, w.id DESC
            LIMIT 5
            """
        ):
            print(dict(row))

        print("\nFlood water-level samples:")
        for row in conn.execute(
            """
            SELECT
                f.id,
                f.station_code,
                s.station_name,
                s.station_type,
                f.observed_at,
                f.water_level_m,
                f.raw_water_level
            FROM flood_water_levels AS f
            LEFT JOIN stations AS s
                ON s.station_code = f.station_code
            ORDER BY f.observed_at DESC, f.id DESC
            LIMIT 5
            """
        ):
            print(dict(row))

        print("\nStation samples:")
        for row in conn.execute(
            """
            SELECT station_code, station_name, station_type
            FROM stations
            ORDER BY station_code
            LIMIT 5
            """
        ):
            print(dict(row))

        print("\nsource_imports:")
        for row in conn.execute(
            """
            SELECT source_file, source_format, imported_at, row_count
            FROM source_imports
            ORDER BY id
            """
        ):
            print(dict(row))


if __name__ == "__main__":
    main()
