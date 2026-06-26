#!/usr/bin/env python3
"""Create the local coordinate candidate table for Day 7."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = PROJECT_ROOT / "data" / "local" / "shenzhen_water.db"


def create_location_candidates_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS location_candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_code TEXT NOT NULL,
            longitude REAL NOT NULL,
            latitude REAL NOT NULL,
            formatted_address TEXT NOT NULL,
            amap_level TEXT,
            amap_adcode TEXT,
            coord_source TEXT NOT NULL,
            coord_quality TEXT NOT NULL,
            review_status TEXT NOT NULL,
            reviewed_at TEXT,
            review_note TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (station_code) REFERENCES stations (station_code)
        );

        CREATE INDEX IF NOT EXISTS idx_location_candidates_station_status
            ON location_candidates (station_code, review_status, reviewed_at, id);
        """
    )


def migrate(db_path: Path = DEFAULT_DB) -> None:
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    with sqlite3.connect(db_path) as conn:
        create_location_candidates_schema(conn)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create the Day 7 coordinate candidate schema."
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite database path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    migrate(args.db)
    print(f"location_candidates schema ready: {args.db}")


if __name__ == "__main__":
    main()
