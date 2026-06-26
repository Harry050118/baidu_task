from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient


class FakeGeocoder:
    def geocode(self, address: str, city: str = "深圳") -> dict[str, Any]:
        return {
            "status": "1",
            "info": "OK",
            "infocode": "10000",
            "count": "1",
            "geocodes": [
                {
                    "formatted_address": "广东省深圳市龙岗区南联第六工业区桥洞",
                    "location": "114.258123,22.723456",
                    "level": "兴趣点",
                    "adcode": "440307",
                }
            ],
        }


class MissingKeyGeocoder:
    def geocode(self, address: str, city: str = "深圳") -> dict[str, Any]:
        from backend.app.services.coordinates.amap_geocoder import MissingAmapKeyError

        raise MissingAmapKeyError("AMAP_WEB_SERVICE_KEY is not configured")


def create_base_database(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
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
                water_level_m REAL NOT NULL,
                raw_water_level TEXT NOT NULL,
                source_file TEXT NOT NULL,
                imported_at TEXT NOT NULL
            );

            CREATE TABLE reservoir_water_levels (
                id TEXT PRIMARY KEY,
                station_code TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                water_level_m REAL,
                raw_water_level TEXT NOT NULL,
                source_file TEXT NOT NULL,
                imported_at TEXT NOT NULL
            );

            CREATE TABLE source_imports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT NOT NULL,
                source_format TEXT NOT NULL,
                imported_at TEXT NOT NULL,
                row_count INTEGER NOT NULL
            );

            INSERT INTO stations (
                station_code,
                station_name,
                station_type,
                source_file,
                imported_at
            ) VALUES
                (
                    '9281192008',
                    '(市)南联第六工业区桥洞',
                    '内涝水情站',
                    'stations.csv',
                    '2026-06-23T06:43:59+00:00'
                ),
                (
                    'MS1068110543000000',
                    '坪地长坑水库',
                    '水库水位站',
                    'stations.csv',
                    '2026-06-23T06:43:59+00:00'
                );

            INSERT INTO flood_water_levels (
                id,
                station_code,
                observed_at,
                water_level_m,
                raw_water_level,
                source_file,
                imported_at
            ) VALUES (
                'F1',
                '9281192008',
                '2026-06-23 00:47:39',
                0.12,
                '0.12',
                'flood.csv',
                '2026-06-23T06:43:59+00:00'
            );
            """
        )


def create_test_client(
    db_path: Path,
    geocoder: object | None = None,
) -> TestClient:
    from backend.app.api.routes import create_api_router
    from backend.app.core.config import Settings
    from backend.app.repositories.water_repository import WaterRepository

    settings = Settings(database_url=f"sqlite:///{db_path}")
    repository = WaterRepository(settings)
    app = FastAPI()
    app.include_router(
        create_api_router(repository, geocoder=geocoder or FakeGeocoder()),
        prefix="/api",
    )
    return TestClient(app)


class BackendDay7MigrationTest(unittest.TestCase):
    def test_migration_creates_empty_location_candidate_table(self) -> None:
        from scripts import migrate_location_candidates_sqlite as migration

        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            create_base_database(db_path)

            migration.migrate(db_path)

            with sqlite3.connect(db_path) as conn:
                table_names = {
                    row[0]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    )
                }
                candidate_count = conn.execute(
                    "SELECT COUNT(*) FROM location_candidates"
                ).fetchone()[0]
                station_count = conn.execute("SELECT COUNT(*) FROM stations").fetchone()[0]

        self.assertIn("location_candidates", table_names)
        self.assertEqual(candidate_count, 0)
        self.assertEqual(station_count, 2)


class BackendDay7LocationApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        create_base_database(self.db_path)
        from scripts import migrate_location_candidates_sqlite as migration

        migration.migrate(self.db_path)
        self.client = create_test_client(self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_locations_status_reports_coordinate_gap_and_candidate_counts(self) -> None:
        response = self.client.get("/api/locations/status")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total_stations"], 2)
        self.assertFalse(payload["has_coordinate_columns"])
        self.assertEqual(payload["coordinate_status"], "missing_coordinates")
        self.assertEqual(payload["candidate_count"], 0)
        self.assertEqual(payload["approved_count"], 0)
        self.assertEqual(payload["rejected_count"], 0)
        self.assertEqual(
            payload["required_action"],
            "coordinate_source_and_manual_review_required",
        )

    def test_unknown_station_returns_404_for_location_flows(self) -> None:
        create_response = self.client.post(
            "/api/locations/geocode-candidates",
            json={"station_code": "not-a-station"},
        )
        list_response = self.client.get("/api/locations/not-a-station/candidates")
        review_response = self.client.post(
            "/api/locations/not-a-station/review",
            json={"candidate_id": 1, "review_status": "approved"},
        )

        self.assertEqual(create_response.status_code, 404)
        self.assertEqual(list_response.status_code, 404)
        self.assertEqual(review_response.status_code, 404)

    def test_geocode_candidates_rejects_batch_payload(self) -> None:
        response = self.client.post(
            "/api/locations/geocode-candidates",
            json=[{"station_code": "9281192008"}],
        )

        self.assertEqual(response.status_code, 422)

    def test_missing_amap_key_returns_503_without_leaking_key_material(self) -> None:
        client = create_test_client(self.db_path, geocoder=MissingKeyGeocoder())

        response = client.post(
            "/api/locations/geocode-candidates",
            json={"station_code": "9281192008"},
        )

        self.assertEqual(response.status_code, 503)
        payload_text = response.text
        self.assertNotIn("key=", payload_text)
        self.assertNotIn("AMAP_WEB_SERVICE_KEY=", payload_text)

    def test_single_station_geocode_candidate_can_be_saved_and_listed(self) -> None:
        response = self.client.post(
            "/api/locations/geocode-candidates",
            json={"station_code": "9281192008"},
        )

        self.assertEqual(response.status_code, 200)
        candidate = response.json()["candidate"]
        self.assertEqual(candidate["station_code"], "9281192008")
        self.assertEqual(candidate["longitude"], 114.258123)
        self.assertEqual(candidate["latitude"], 22.723456)
        self.assertEqual(candidate["coord_source"], "amap")
        self.assertEqual(candidate["coord_quality"], "candidate")
        self.assertEqual(candidate["review_status"], "pending")
        self.assertEqual(response.json()["amap_status"]["infocode"], "10000")
        self.assertNotIn("request_url", response.json())

        list_response = self.client.get("/api/locations/9281192008/candidates")

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.json()["station"]["station_code"], "9281192008")
        self.assertEqual(list_response.json()["items"], [candidate])

    def test_review_updates_candidate_status(self) -> None:
        candidate = self.client.post(
            "/api/locations/geocode-candidates",
            json={"station_code": "9281192008"},
        ).json()["candidate"]

        response = self.client.post(
            "/api/locations/9281192008/review",
            json={
                "candidate_id": candidate["id"],
                "review_status": "approved",
                "review_note": "人工核验可用",
            },
        )

        self.assertEqual(response.status_code, 200)
        reviewed = response.json()["candidate"]
        self.assertEqual(reviewed["review_status"], "approved")
        self.assertEqual(reviewed["coord_quality"], "verified")
        self.assertEqual(reviewed["review_note"], "人工核验可用")
        self.assertIsNotNone(reviewed["reviewed_at"])

    def test_pending_candidate_does_not_enter_map_points_but_approved_candidate_does(
        self,
    ) -> None:
        candidate = self.client.post(
            "/api/locations/geocode-candidates",
            json={"station_code": "9281192008"},
        ).json()["candidate"]

        pending_point = self.client.get("/api/map/points").json()["points"][0]

        self.assertFalse(pending_point["has_coordinates"])
        self.assertEqual(pending_point["coordinate_status"], "missing_coordinates")
        self.assertNotIn("longitude", pending_point)
        self.assertNotIn("latitude", pending_point)

        self.client.post(
            "/api/locations/9281192008/review",
            json={"candidate_id": candidate["id"], "review_status": "approved"},
        )

        approved_point = self.client.get("/api/map/points").json()["points"][0]

        self.assertTrue(approved_point["has_coordinates"])
        self.assertEqual(approved_point["coordinate_status"], "approved")
        self.assertEqual(approved_point["longitude"], 114.258123)
        self.assertEqual(approved_point["latitude"], 22.723456)
        self.assertEqual(approved_point["coord_source"], "amap")
        self.assertEqual(approved_point["coord_quality"], "verified")
        self.assertEqual(approved_point["review_status"], "approved")


if __name__ == "__main__":
    unittest.main()
