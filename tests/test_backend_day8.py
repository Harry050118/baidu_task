from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from backend.app.main import app


class BackendDay8AssessmentApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health_check_still_reports_database_ready(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_assessments_return_flood_station_rule_results(self) -> None:
        response = self.client.get("/api/assessments")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        assessments = payload["items"]
        self.assertEqual(len(assessments), 148)
        self.assertNotIn("reservoir_water_levels", payload)

        station_codes = {item["station_code"] for item in assessments}
        self.assertEqual(len(station_codes), 148)
        self.assertIn("9281192008", station_codes)
        self.assertNotIn("MS1068110543000000", station_codes)

        for item in assessments:
            self.assertEqual(item["rule_version"], "flood_rule_v1")
            self.assertIn(item["risk_level"], {
                "no_data",
                "normal",
                "attention",
                "warning",
                "danger",
            })
            self.assertIn(item["trend"], {
                "no_data",
                "stable",
                "rising",
                "falling",
                "fluctuating",
            })
            self.assertIn("station_name", item)
            self.assertIn("latest_observed_at", item)
            self.assertIn("latest_water_level_m", item)
            self.assertIn("rule_description", item)
            self.assertIn("generated_at", item)

    def test_single_point_assessment_returns_real_flood_station(self) -> None:
        response = self.client.get("/api/points/9281192008/assessment")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["station_code"], "9281192008")
        self.assertEqual(payload["station_name"], "(市)南联第六工业区桥洞")
        self.assertEqual(payload["latest_water_level_m"], 0.0)
        self.assertEqual(payload["risk_level"], "normal")
        self.assertEqual(payload["trend"], "stable")
        self.assertEqual(payload["rule_version"], "flood_rule_v1")
        self.assertNotIn("reservoir_water_levels", payload)

    def test_unknown_or_non_flood_station_assessment_returns_404(self) -> None:
        unknown_response = self.client.get("/api/points/not-a-station/assessment")
        reservoir_response = self.client.get(
            "/api/points/MS1068110543000000/assessment"
        )

        self.assertEqual(unknown_response.status_code, 404)
        self.assertEqual(unknown_response.json()["detail"], "flood station not found")
        self.assertEqual(reservoir_response.status_code, 404)
        self.assertEqual(reservoir_response.json()["detail"], "flood station not found")


class BackendDay8AssessmentRuleTest(unittest.TestCase):
    def test_risk_level_thresholds(self) -> None:
        from backend.app.services.assessments import assess_risk_level

        cases = [
            (None, "no_data"),
            (0.14, "normal"),
            (0.15, "attention"),
            (0.29, "attention"),
            (0.30, "warning"),
            (0.49, "warning"),
            (0.50, "danger"),
        ]

        for water_level, expected in cases:
            with self.subTest(water_level=water_level):
                self.assertEqual(assess_risk_level(water_level), expected)

    def test_trend_rules(self) -> None:
        from backend.app.services.assessments import assess_trend

        cases = [
            ([], "no_data"),
            ([0.10], "stable"),
            ([0.10, 0.11, 0.12], "stable"),
            ([0.10, 0.13, 0.18], "rising"),
            ([0.18, 0.13, 0.10], "falling"),
            ([0.10, 0.18, 0.12, 0.20], "fluctuating"),
        ]

        for water_levels, expected in cases:
            with self.subTest(water_levels=water_levels):
                self.assertEqual(assess_trend(water_levels), expected)


if __name__ == "__main__":
    unittest.main()
