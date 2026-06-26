from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from fastapi.testclient import TestClient

from backend.app.main import app


class MissingKeyGeocoder:
    def geocode(self, address: str, city: str = "深圳") -> dict[str, Any]:
        from backend.app.services.coordinates.amap_geocoder import MissingAmapKeyError

        raise MissingAmapKeyError("AMAP_WEB_SERVICE_KEY is not configured")


class BackendDay9FrontendContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_service_starts_and_health_contract_is_stable(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["database"]["status"], "ok")
        self.assertIsInstance(payload["database"]["path"], str)
        self.assertIn("flood_water_levels", payload["database"]["tables"])

    def test_key_api_top_level_response_shapes_are_stable(self) -> None:
        cases = [
            ("/api/map/points", {"points"}),
            ("/api/points/9281192008", {"station", "latest_water_level", "coordinates"}),
            ("/api/points/9281192008/history?limit=2", {"station", "items"}),
            ("/api/data/time-range", {"flood_water_levels", "reservoir_water_levels"}),
            ("/api/stats/overview", {
                "flood_station_count",
                "latest_observed_at",
                "flood_record_count",
                "stations_total",
                "coordinate_status",
                "has_coordinates",
            }),
            ("/api/stats/stations", {
                "total",
                "district_stats_available",
                "district_stats_reason",
                "items",
            }),
            ("/api/status/data", {
                "flood_water_levels",
                "stations",
                "reservoir_water_levels",
                "data_freshness",
            }),
            ("/api/imports/latest", {
                "latest_imported_at",
                "import_count",
                "total_row_count",
                "items",
            }),
            ("/api/locations/status", {
                "total_stations",
                "has_coordinate_columns",
                "coordinate_status",
                "candidate_count",
                "approved_count",
                "rejected_count",
                "required_action",
            }),
            ("/api/locations/9281192008/candidates", {"station", "items"}),
            ("/api/assessments", {"items"}),
            ("/api/points/9281192008/assessment", {
                "station_code",
                "station_name",
                "latest_observed_at",
                "latest_water_level_m",
                "risk_level",
                "trend",
                "rule_version",
                "rule_description",
                "generated_at",
            }),
        ]

        for path, expected_keys in cases:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(set(response.json()), expected_keys)

    def test_error_contracts_are_stable(self) -> None:
        not_found = self.client.get("/api/points/not-a-station")
        validation_error = self.client.get("/api/points/9281192008/history?limit=5001")

        self.assertEqual(not_found.status_code, 404)
        self.assertEqual(not_found.json(), {"detail": "flood station not found"})
        self.assertEqual(validation_error.status_code, 422)
        self.assertIn("detail", validation_error.json())

    def test_reservoir_data_stays_out_of_map_and_risk_mainline(self) -> None:
        map_payload = self.client.get("/api/map/points").json()
        detail_payload = self.client.get("/api/points/9281192008").json()
        history_payload = self.client.get("/api/points/9281192008/history?limit=1").json()
        stats_payload = self.client.get("/api/stats/overview").json()
        assessments_payload = self.client.get("/api/assessments").json()

        for payload in [
            map_payload,
            detail_payload,
            history_payload,
            stats_payload,
            assessments_payload,
        ]:
            with self.subTest(payload_keys=set(payload)):
                self.assertNotIn("reservoir_water_levels", payload)

        self.assertEqual(
            self.client.get("/api/data/time-range").json()["reservoir_water_levels"][
                "quality_role"
            ],
            "status_summary_only",
        )
        self.assertEqual(
            self.client.get("/api/status/data").json()["reservoir_water_levels"][
                "quality_role"
            ],
            "status_summary_only",
        )


class BackendDay9SensitiveErrorTest(unittest.TestCase):
    def test_missing_amap_key_returns_503_without_secret_material(self) -> None:
        from backend.app.api.routes import create_api_router
        from backend.app.core.config import Settings
        from backend.app.repositories.water_repository import WaterRepository

        settings = Settings(
            database_url="sqlite:///data/local/shenzhen_water.db",
            amap_web_service_key="day9-secret-key",
        )
        repository = WaterRepository(settings)
        from fastapi import FastAPI

        test_app = FastAPI()
        test_app.include_router(
            create_api_router(repository, geocoder=MissingKeyGeocoder()),
            prefix="/api",
        )

        response = TestClient(test_app).post(
            "/api/locations/geocode-candidates",
            json={"station_code": "9281192008"},
        )

        self.assertEqual(response.status_code, 503)
        response_text = response.text
        self.assertNotIn("day9-secret-key", response_text)
        self.assertNotIn("AMAP_WEB_SERVICE_KEY=", response_text)
        self.assertNotIn("key=", response_text)

    def test_missing_database_returns_503_without_filesystem_traceback(self) -> None:
        from backend.app.core.config import Settings
        from backend.app.main import create_app

        with TemporaryDirectory() as temp_dir:
            missing_db = Path(temp_dir) / "missing.db"
            response = TestClient(
                create_app(Settings(database_url=f"sqlite:///{missing_db}"))
            ).get("/health")

        self.assertEqual(response.status_code, 503)
        payload = response.json()
        self.assertEqual(payload["detail"], "database unavailable")
        self.assertNotIn("Traceback", response.text)
        self.assertNotIn(str(missing_db), response.text)


if __name__ == "__main__":
    unittest.main()
