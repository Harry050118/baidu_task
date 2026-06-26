from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "data" / "local" / "shenzhen_water.db"


class BackendDay4RepositoryTest(unittest.TestCase):
    def test_repository_reports_day3_database_facts(self) -> None:
        from backend.app.core.config import Settings
        from backend.app.repositories.water_repository import WaterRepository

        repository = WaterRepository(Settings(database_url=f"sqlite:///{DATABASE_PATH}"))

        summary = repository.get_database_summary()

        self.assertEqual(summary["stations"]["rows"], 485)
        self.assertEqual(summary["flood_water_levels"]["rows"], 4_101_063)
        self.assertEqual(summary["flood_water_levels"]["unique_station_codes"], 148)
        self.assertEqual(summary["flood_water_levels"]["matched_station_codes"], 148)
        self.assertEqual(summary["flood_water_levels"]["missing_station_codes"], 0)
        self.assertEqual(
            summary["flood_water_levels"]["observed_at_min"],
            "2025-12-31 23:50:23",
        )
        self.assertEqual(
            summary["flood_water_levels"]["observed_at_max"],
            "2026-06-23 00:47:39",
        )
        self.assertEqual(summary["reservoir_water_levels"]["rows"], 2_040_352)
        self.assertEqual(summary["reservoir_water_levels"]["unique_station_codes"], 178)
        self.assertEqual(summary["reservoir_water_levels"]["null_water_level_rows"], 40_982)
        self.assertEqual(summary["reservoir_water_levels"]["missing_station_codes"], 9)

    def test_latest_flood_levels_are_joined_to_station_metadata(self) -> None:
        from backend.app.core.config import Settings
        from backend.app.repositories.water_repository import WaterRepository

        repository = WaterRepository(Settings(database_url=f"sqlite:///{DATABASE_PATH}"))

        rows = repository.get_latest_flood_water_levels(limit=3)

        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertEqual(row["station_type"], "内涝水情站")
            self.assertIsInstance(row["station_code"], str)
            self.assertIsInstance(row["station_name"], str)
            self.assertIsInstance(row["water_level_m"], float)
            self.assertIsInstance(row["observed_at"], str)

    def test_station_coordinate_status_reports_missing_fields(self) -> None:
        from backend.app.core.config import Settings
        from backend.app.repositories.water_repository import WaterRepository

        repository = WaterRepository(Settings(database_url=f"sqlite:///{DATABASE_PATH}"))

        status = repository.get_station_coordinate_status()

        self.assertFalse(status["has_coordinate_columns"])
        self.assertEqual(status["total_stations"], 485)
        self.assertEqual(status["missing_coordinate_stations"], 485)
        self.assertEqual(status["status"], "missing_coordinates")

    def test_sqlite_connection_is_opened_read_only(self) -> None:
        from backend.app.core.config import Settings
        from backend.app.core.database import connect_readonly

        with connect_readonly(Settings(database_url=f"sqlite:///{DATABASE_PATH}")) as conn:
            with self.assertRaises(sqlite3.OperationalError):
                conn.execute(
                    "CREATE TABLE day4_readonly_probe (id INTEGER PRIMARY KEY)"
                )


class BackendDay4HealthCheckTest(unittest.TestCase):
    def test_health_check_reports_database_ready(self) -> None:
        from fastapi.testclient import TestClient

        from backend.app.main import app

        response = TestClient(app).get("/health")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["database"]["status"], "ok")
        self.assertEqual(payload["database"]["path"], str(DATABASE_PATH))
        self.assertEqual(
            payload["database"]["tables"],
            [
                "flood_water_levels",
                "location_candidates",
                "reservoir_water_levels",
                "source_imports",
                "stations",
            ],
        )


if __name__ == "__main__":
    unittest.main()
