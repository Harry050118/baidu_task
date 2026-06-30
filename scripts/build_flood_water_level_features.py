#!/usr/bin/env python3
"""Build Day 13 flood water-level feature outputs from the local SQLite database."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sqlite3
import sys
from collections import Counter, deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.assessments import assess_risk_level, assess_trend

DEFAULT_DB = PROJECT_ROOT / "data" / "local" / "shenzhen_water.db"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "features" / "flood_water_level_features_day13.csv"
DEFAULT_QUALITY_OUTPUT = (
    PROJECT_ROOT / "data" / "features" / "flood_water_level_features_day13_quality.json"
)

ABNORMAL_INTERVAL_SECONDS = 21_600
INSTANT_JUMP_DELTA_M = 0.20
INSTANT_JUMP_MAX_SECONDS = 3_600

FIELDNAMES = [
    "station_code",
    "station_name",
    "observed_at",
    "water_level_m",
    "previous_observed_at",
    "previous_water_level_m",
    "water_level_delta_m",
    "seconds_since_previous",
    "water_level_velocity_m_per_s",
    "recent_valid_level_m",
    "consecutive_rising_count",
    "consecutive_falling_count",
    "has_coordinates",
    "coord_source",
    "coord_quality",
    "review_status",
    "risk_level_rule_v1",
    "trend_rule_v1",
]


@dataclass
class StationFeatureState:
    previous_observed_at: str | None = None
    previous_water_level_m: float | None = None
    recent_valid_level_m: float | None = None
    consecutive_rising_count: int = 0
    consecutive_falling_count: int = 0
    recent_levels: deque[float] = field(default_factory=lambda: deque(maxlen=6))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Day 13 flood water-level feature CSV and quality JSON."
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite database path")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Feature CSV output path",
    )
    parser.add_argument(
        "--quality-output",
        type=Path,
        default=DEFAULT_QUALITY_OUTPUT,
        help="Quality summary JSON output path",
    )
    return parser.parse_args()


def connect_database(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
            AND name = ?
        """,
        (table_name,),
    ).fetchone()
    return row is not None


def read_stations(conn: sqlite3.Connection) -> dict[str, str]:
    rows = conn.execute(
        """
        SELECT station_code, station_name
        FROM stations
        """
    ).fetchall()
    return {row["station_code"]: row["station_name"] for row in rows}


def read_approved_locations(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    if not table_exists(conn, "location_candidates"):
        return {}

    rows = conn.execute(
        """
        WITH approved_locations AS (
            SELECT
                station_code,
                coord_source,
                coord_quality,
                review_status,
                ROW_NUMBER() OVER (
                    PARTITION BY station_code
                    ORDER BY reviewed_at DESC, updated_at DESC, id DESC
                ) AS row_number
            FROM location_candidates
            WHERE review_status = 'approved'
        )
        SELECT station_code, coord_source, coord_quality, review_status
        FROM approved_locations
        WHERE row_number = 1
        """
    ).fetchall()
    return {row["station_code"]: dict(row) for row in rows}


def iter_water_levels(conn: sqlite3.Connection) -> Any:
    return conn.execute(
        """
        SELECT id, station_code, observed_at, water_level_m
        FROM flood_water_levels
        ORDER BY station_code, observed_at, id
        """
    )


def parse_observed_at(value: str) -> datetime:
    return datetime.fromisoformat(value)


def seconds_between(current_observed_at: str, previous_observed_at: str) -> int:
    current = parse_observed_at(current_observed_at)
    previous = parse_observed_at(previous_observed_at)
    return int((current - previous).total_seconds())


def format_float(value: float | None, *, places: int = 12) -> str:
    if value is None:
        return ""
    text = f"{value:.{places}f}".rstrip("0").rstrip(".")
    if text == "-0":
        return "0"
    return text


def format_int(value: int | None) -> str:
    return "" if value is None else str(value)


def build_feature_row(
    *,
    row: sqlite3.Row,
    station_name: str,
    location: dict[str, Any] | None,
    state: StationFeatureState,
) -> tuple[dict[str, str], int | None, float | None]:
    water_level = row["water_level_m"]
    previous_observed_at = state.previous_observed_at
    previous_water_level = state.previous_water_level_m
    delta: float | None = None
    elapsed_seconds: int | None = None
    velocity: float | None = None

    if water_level is not None and previous_observed_at is not None:
        delta = water_level - previous_water_level
        elapsed_seconds = seconds_between(row["observed_at"], previous_observed_at)
        if elapsed_seconds > 0:
            velocity = delta / elapsed_seconds

        if delta > 0:
            state.consecutive_rising_count += 1
            state.consecutive_falling_count = 0
        elif delta < 0:
            state.consecutive_falling_count += 1
            state.consecutive_rising_count = 0
        else:
            state.consecutive_rising_count = 0
            state.consecutive_falling_count = 0

    if water_level is not None:
        state.previous_observed_at = row["observed_at"]
        state.previous_water_level_m = water_level
        state.recent_valid_level_m = water_level
        state.recent_levels.append(water_level)

    has_coordinates = location is not None
    feature_row = {
        "station_code": row["station_code"],
        "station_name": station_name,
        "observed_at": row["observed_at"],
        "water_level_m": format_float(water_level),
        "previous_observed_at": previous_observed_at or "",
        "previous_water_level_m": format_float(previous_water_level),
        "water_level_delta_m": format_float(delta),
        "seconds_since_previous": format_int(elapsed_seconds),
        "water_level_velocity_m_per_s": format_float(velocity),
        "recent_valid_level_m": format_float(state.recent_valid_level_m),
        "consecutive_rising_count": str(state.consecutive_rising_count),
        "consecutive_falling_count": str(state.consecutive_falling_count),
        "has_coordinates": "true" if has_coordinates else "false",
        "coord_source": location["coord_source"] if location else "",
        "coord_quality": location["coord_quality"] if location else "",
        "review_status": location["review_status"] if location else "",
        "risk_level_rule_v1": assess_risk_level(water_level),
        "trend_rule_v1": assess_trend(list(state.recent_levels)),
    }
    return feature_row, elapsed_seconds, delta


def percentile_nearest_rank(values: list[int], percentile: float) -> int:
    if not values:
        return 0
    index = max(0, math.ceil(len(values) * percentile) - 1)
    return values[index]


def summarize_station_samples(sample_counts: Counter[str]) -> dict[str, float | int]:
    counts = sorted(sample_counts.values())
    if not counts:
        return {"min": 0, "p25": 0, "median": 0, "p75": 0, "max": 0, "average": 0}
    return {
        "min": counts[0],
        "p25": percentile_nearest_rank(counts, 0.25),
        "median": percentile_nearest_rank(counts, 0.50),
        "p75": percentile_nearest_rank(counts, 0.75),
        "max": counts[-1],
        "average": round(sum(counts) / len(counts), 2),
    }


def build_feature_outputs(
    db_path: Path,
    output_path: Path,
    quality_output_path: Path,
) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    quality_output_path.parent.mkdir(parents=True, exist_ok=True)

    total_records = 0
    null_water_level_count = 0
    zero_water_level_count = 0
    nonzero_water_level_count = 0
    abnormal_interval_count = 0
    instant_jump_candidate_count = 0
    sample_counts: Counter[str] = Counter()
    station_codes: set[str] = set()
    states: dict[str, StationFeatureState] = {}

    with connect_database(db_path) as conn:
        stations = read_stations(conn)
        approved_locations = read_approved_locations(conn)
        with output_path.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writeheader()

            for row in iter_water_levels(conn):
                station_code = row["station_code"]
                station_codes.add(station_code)
                sample_counts[station_code] += 1
                total_records += 1

                water_level = row["water_level_m"]
                if water_level is None:
                    null_water_level_count += 1
                elif water_level == 0:
                    zero_water_level_count += 1
                else:
                    nonzero_water_level_count += 1

                state = states.setdefault(station_code, StationFeatureState())
                feature_row, elapsed_seconds, delta = build_feature_row(
                    row=row,
                    station_name=stations.get(station_code, ""),
                    location=approved_locations.get(station_code),
                    state=state,
                )
                writer.writerow(feature_row)

                if elapsed_seconds is not None and (
                    elapsed_seconds <= 0
                    or elapsed_seconds > ABNORMAL_INTERVAL_SECONDS
                ):
                    abnormal_interval_count += 1
                if (
                    delta is not None
                    and elapsed_seconds is not None
                    and abs(delta) >= INSTANT_JUMP_DELTA_M
                    and 0 < elapsed_seconds <= INSTANT_JUMP_MAX_SECONDS
                ):
                    instant_jump_candidate_count += 1

    quality = {
        "feature_file": str(output_path),
        "total_records": total_records,
        "station_count": len(station_codes),
        "null_water_level_count": null_water_level_count,
        "zero_water_level_count": zero_water_level_count,
        "nonzero_water_level_count": nonzero_water_level_count,
        "abnormal_interval_count": abnormal_interval_count,
        "instant_jump_candidate_count": instant_jump_candidate_count,
        "station_sample_distribution": summarize_station_samples(sample_counts),
        "thresholds": {
            "abnormal_interval_seconds": ABNORMAL_INTERVAL_SECONDS,
            "instant_jump_delta_m": INSTANT_JUMP_DELTA_M,
            "instant_jump_max_seconds": INSTANT_JUMP_MAX_SECONDS,
        },
    }
    quality_output_path.write_text(
        json.dumps(quality, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return quality


def main() -> None:
    args = parse_args()
    quality = build_feature_outputs(args.db, args.output, args.quality_output)
    print(f"Generated feature CSV: {args.output}")
    print(f"Generated quality summary: {args.quality_output}")
    print(json.dumps(quality, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
