from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from backend.app.main import app


class BackendDay6StatsApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_stats_overview_reports_mainline_flood_facts(self) -> None:
        response = self.client.get("/api/stats/overview")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["flood_station_count"], 148)
        self.assertEqual(payload["latest_observed_at"], "2026-06-23 00:47:39")
        self.assertEqual(payload["flood_record_count"], 4_101_063)
        self.assertEqual(payload["stations_total"], 485)
        self.assertEqual(payload["coordinate_status"], "missing_coordinates")
        self.assertFalse(payload["has_coordinates"])
        self.assertNotIn("risk_levels", payload)
        self.assertNotIn("reservoir_water_levels", payload)


class BackendDay6DataStatusApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_status_data_reports_coordinate_gap_and_reservoir_quality_side_channel(
        self,
    ) -> None:
        response = self.client.get("/api/status/data")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["flood_water_levels"]["record_count"], 4_101_063)
        self.assertEqual(payload["flood_water_levels"]["unique_station_codes"], 148)
        self.assertTrue(payload["flood_water_levels"]["map_query_ready"])
        self.assertFalse(payload["flood_water_levels"]["real_map_placement_ready"])
        self.assertEqual(payload["stations"]["total"], 485)
        self.assertEqual(payload["stations"]["coordinate_status"], "missing_coordinates")
        self.assertFalse(payload["stations"]["has_coordinates"])
        self.assertEqual(payload["stations"]["missing_coordinate_stations"], 485)
        self.assertEqual(
            payload["reservoir_water_levels"]["quality_role"],
            "status_summary_only",
        )
        self.assertEqual(payload["reservoir_water_levels"]["record_count"], 2_040_352)
        self.assertEqual(
            payload["reservoir_water_levels"]["null_water_level_rows"],
            40_982,
        )
        self.assertEqual(payload["data_freshness"]["status"], "historical_snapshot")
        self.assertEqual(
            payload["data_freshness"]["latest_observed_at"],
            "2026-06-23 00:47:39",
        )


class BackendDay6ImportsApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_imports_latest_returns_real_source_import_rows(self) -> None:
        response = self.client.get("/api/imports/latest")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["latest_imported_at"], "2026-06-23T06:43:59+00:00")
        self.assertEqual(payload["import_count"], 13)
        self.assertEqual(payload["total_row_count"], 6_141_915)
        self.assertEqual(len(payload["items"]), 13)
        self.assertEqual(payload["items"][0]["id"], 7)
        self.assertEqual(payload["items"][-1]["id"], 19)
        for item in payload["items"]:
            self.assertEqual(item["source_format"], "csv")
            self.assertIn("source_file", item)
            self.assertIn("row_count", item)
            self.assertNotIn("status", item)
            self.assertNotIn("error", item)


if __name__ == "__main__":
    unittest.main()
