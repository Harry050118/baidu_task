from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from backend.app.main import app


class BackendDay5MapApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_map_points_return_all_flood_stations_without_coordinates(self) -> None:
        response = self.client.get("/api/map/points")

        self.assertEqual(response.status_code, 200)
        points = response.json()["points"]
        self.assertEqual(len(points), 148)

        station_codes = {point["station_code"] for point in points}
        self.assertEqual(len(station_codes), 148)
        for point in points:
            self.assertEqual(point["station_type"], "内涝水情站")
            self.assertIn("station_name", point)
            self.assertIn("latest_observed_at", point)
            self.assertIn("latest_water_level_m", point)
            self.assertIn("raw_water_level", point)
            self.assertFalse(point["has_coordinates"])
            self.assertEqual(point["coordinate_status"], "missing_coordinates")
            self.assertNotIn("longitude", point)
            self.assertNotIn("latitude", point)

    def test_data_time_range_reports_day3_flood_facts(self) -> None:
        response = self.client.get("/api/data/time-range")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(
            payload["flood_water_levels"]["observed_at_min"],
            "2025-12-31 23:50:23",
        )
        self.assertEqual(
            payload["flood_water_levels"]["observed_at_max"],
            "2026-06-23 00:47:39",
        )
        self.assertEqual(
            payload["reservoir_water_levels"]["quality_role"],
            "status_summary_only",
        )


class BackendDay5PointApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_point_detail_returns_latest_flood_level_and_coordinate_status(self) -> None:
        response = self.client.get("/api/points/9281192008")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["station"]["station_code"], "9281192008")
        self.assertEqual(payload["station"]["station_type"], "内涝水情站")
        self.assertFalse(payload["coordinates"]["has_coordinates"])
        self.assertEqual(payload["coordinates"]["coordinate_status"], "missing_coordinates")
        self.assertIn("latest_observed_at", payload["latest_water_level"])
        self.assertIn("latest_water_level_m", payload["latest_water_level"])
        self.assertIn("raw_water_level", payload["latest_water_level"])
        self.assertNotIn("longitude", payload["coordinates"])
        self.assertNotIn("latitude", payload["coordinates"])

    def test_history_returns_real_flood_series_in_descending_time_order(self) -> None:
        response = self.client.get("/api/points/9281192008/history?limit=5")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["station"]["station_code"], "9281192008")
        self.assertEqual(payload["station"]["station_type"], "内涝水情站")
        self.assertEqual(len(payload["items"]), 5)

        observed_times = [item["observed_at"] for item in payload["items"]]
        self.assertEqual(observed_times, sorted(observed_times, reverse=True))
        for item in payload["items"]:
            self.assertEqual(item["station_code"], "9281192008")
            self.assertIsInstance(item["water_level_m"], float)
            self.assertIsInstance(item["raw_water_level"], str)

    def test_unknown_or_non_flood_station_returns_404(self) -> None:
        unknown_response = self.client.get("/api/points/not-a-station")
        reservoir_response = self.client.get("/api/points/MS1068110543000000/history")

        self.assertEqual(unknown_response.status_code, 404)
        self.assertEqual(unknown_response.json()["detail"], "flood station not found")
        self.assertEqual(reservoir_response.status_code, 404)
        self.assertEqual(reservoir_response.json()["detail"], "flood station not found")

    def test_history_limit_is_bounded(self) -> None:
        response = self.client.get("/api/points/9281192008/history?limit=5001")

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
