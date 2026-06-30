from __future__ import annotations

import csv
import json
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts import build_flood_water_level_features as features


def create_schema(conn: sqlite3.Connection, *, with_locations: bool = True) -> None:
    conn.executescript(
        """
        CREATE TABLE stations (
            station_code TEXT PRIMARY KEY,
            station_name TEXT NOT NULL,
            station_type TEXT NOT NULL,
            source_file TEXT NOT NULL,
            imported_at TEXT NOT NULL
        );

        CREATE TABLE flood_water_levels (
            id TEXT PRIMARY KEY,
            station_code TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            water_level_m REAL,
            raw_water_level TEXT NOT NULL,
            source_file TEXT NOT NULL,
            imported_at TEXT NOT NULL
        );
        """
    )
    if with_locations:
        conn.executescript(
            """
            CREATE TABLE location_candidates (
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
                updated_at TEXT NOT NULL
            );
            """
        )


def insert_level(
    conn: sqlite3.Connection,
    level_id: str,
    station_code: str,
    observed_at: str,
    water_level_m: float | None,
) -> None:
    conn.execute(
        """
        INSERT INTO flood_water_levels (
            id,
            station_code,
            observed_at,
            water_level_m,
            raw_water_level,
            source_file,
            imported_at
        ) VALUES (?, ?, ?, ?, ?, 'test.csv', '2026-07-06T00:00:00+00:00')
        """,
        (
            level_id,
            station_code,
            observed_at,
            water_level_m,
            "" if water_level_m is None else str(water_level_m),
        ),
    )


class BuildFloodWaterLevelFeaturesTest(unittest.TestCase):
    def test_builds_water_level_features_and_quality_summary(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            db_path = root / "test.db"
            output_path = root / "features.csv"
            quality_path = root / "quality.json"

            with sqlite3.connect(db_path) as conn:
                create_schema(conn)
                conn.execute(
                    """
                    INSERT INTO stations VALUES (
                        'ST001', '测试一站', '内涝水情站', 'stations.csv',
                        '2026-07-06T00:00:00+00:00'
                    )
                    """
                )
                conn.execute(
                    """
                    INSERT INTO stations VALUES (
                        'ST002', '测试二站', '内涝水情站', 'stations.csv',
                        '2026-07-06T00:00:00+00:00'
                    )
                    """
                )
                insert_level(conn, "F1", "ST001", "2026-01-01 00:00:00", 0.10)
                insert_level(conn, "F2", "ST001", "2026-01-01 00:10:00", 0.15)
                insert_level(conn, "F3", "ST001", "2026-01-01 00:20:00", None)
                insert_level(conn, "F4", "ST001", "2026-01-01 00:30:00", 0.12)
                insert_level(conn, "F5", "ST001", "2026-01-01 00:30:01", 0.50)
                insert_level(conn, "F6", "ST002", "2026-01-01 00:00:00", 0.00)
                insert_level(conn, "F7", "ST002", "2026-01-01 07:00:01", 0.01)
                conn.execute(
                    """
                    INSERT INTO location_candidates (
                        station_code,
                        longitude,
                        latitude,
                        formatted_address,
                        coord_source,
                        coord_quality,
                        review_status,
                        reviewed_at,
                        created_at,
                        updated_at
                    ) VALUES (
                        'ST001', 114.1, 22.6, '测试地址', 'amap', 'verified',
                        'approved', '2026-07-06T00:00:00+00:00',
                        '2026-07-06T00:00:00+00:00',
                        '2026-07-06T00:00:00+00:00'
                    )
                    """
                )

            quality = features.build_feature_outputs(db_path, output_path, quality_path)

            with output_path.open("r", encoding="utf-8-sig") as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(len(rows), 7)
            self.assertEqual(rows[0]["station_code"], "ST001")
            self.assertEqual(rows[0]["previous_observed_at"], "")
            self.assertEqual(rows[0]["previous_water_level_m"], "")
            self.assertEqual(rows[0]["recent_valid_level_m"], "0.1")
            self.assertEqual(rows[0]["consecutive_rising_count"], "0")
            self.assertEqual(rows[0]["consecutive_falling_count"], "0")

            self.assertEqual(rows[1]["previous_observed_at"], "2026-01-01 00:00:00")
            self.assertEqual(rows[1]["previous_water_level_m"], "0.1")
            self.assertEqual(rows[1]["water_level_delta_m"], "0.05")
            self.assertEqual(rows[1]["seconds_since_previous"], "600")
            self.assertEqual(
                rows[1]["water_level_velocity_m_per_s"],
                "0.000083333333",
            )
            self.assertEqual(rows[1]["recent_valid_level_m"], "0.15")
            self.assertEqual(rows[1]["consecutive_rising_count"], "1")
            self.assertEqual(rows[1]["consecutive_falling_count"], "0")
            self.assertEqual(rows[1]["has_coordinates"], "true")
            self.assertEqual(rows[1]["coord_source"], "amap")
            self.assertEqual(rows[1]["coord_quality"], "verified")
            self.assertEqual(rows[1]["review_status"], "approved")

            self.assertEqual(rows[2]["water_level_m"], "")
            self.assertEqual(rows[2]["previous_observed_at"], "2026-01-01 00:10:00")
            self.assertEqual(rows[2]["previous_water_level_m"], "0.15")
            self.assertEqual(rows[2]["water_level_delta_m"], "")
            self.assertEqual(rows[2]["seconds_since_previous"], "")
            self.assertEqual(rows[2]["recent_valid_level_m"], "0.15")
            self.assertEqual(rows[2]["consecutive_rising_count"], "1")
            self.assertEqual(rows[2]["consecutive_falling_count"], "0")

            self.assertEqual(rows[3]["previous_observed_at"], "2026-01-01 00:10:00")
            self.assertEqual(rows[3]["water_level_delta_m"], "-0.03")
            self.assertEqual(rows[3]["seconds_since_previous"], "1200")
            self.assertEqual(rows[3]["consecutive_rising_count"], "0")
            self.assertEqual(rows[3]["consecutive_falling_count"], "1")

            self.assertEqual(rows[4]["seconds_since_previous"], "1")
            self.assertEqual(rows[4]["water_level_delta_m"], "0.38")
            self.assertEqual(rows[4]["consecutive_rising_count"], "1")
            self.assertEqual(rows[4]["consecutive_falling_count"], "0")

            self.assertEqual(rows[5]["station_code"], "ST002")
            self.assertEqual(rows[5]["has_coordinates"], "false")
            self.assertEqual(rows[5]["coord_source"], "")

            self.assertEqual(quality["total_records"], 7)
            self.assertEqual(quality["station_count"], 2)
            self.assertEqual(quality["null_water_level_count"], 1)
            self.assertEqual(quality["zero_water_level_count"], 1)
            self.assertEqual(quality["nonzero_water_level_count"], 5)
            self.assertEqual(quality["abnormal_interval_count"], 1)
            self.assertEqual(quality["instant_jump_candidate_count"], 1)
            self.assertEqual(
                quality["station_sample_distribution"],
                {"min": 2, "p25": 2, "median": 2, "p75": 5, "max": 5, "average": 3.5},
            )

            persisted_quality = json.loads(quality_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted_quality, quality)

    def test_builds_without_location_candidates_table(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            db_path = root / "test.db"
            output_path = root / "features.csv"
            quality_path = root / "quality.json"

            with sqlite3.connect(db_path) as conn:
                create_schema(conn, with_locations=False)
                conn.execute(
                    """
                    INSERT INTO stations VALUES (
                        'ST001', '测试一站', '内涝水情站', 'stations.csv',
                        '2026-07-06T00:00:00+00:00'
                    )
                    """
                )
                insert_level(conn, "F1", "ST001", "2026-01-01 00:00:00", 0.10)

            features.build_feature_outputs(db_path, output_path, quality_path)

            with output_path.open("r", encoding="utf-8-sig") as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(rows[0]["has_coordinates"], "false")
            self.assertEqual(rows[0]["coord_source"], "")
            self.assertEqual(rows[0]["coord_quality"], "")
            self.assertEqual(rows[0]["review_status"], "")


if __name__ == "__main__":
    unittest.main()
