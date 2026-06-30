from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts import build_flood_water_level_anomalies_day14 as day14


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


def write_feature_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            base = {fieldname: "" for fieldname in FIELDNAMES}
            base.update(row)
            writer.writerow(base)


def feature_row(
    station_code: str,
    station_name: str,
    observed_at: str,
    water_level_m: str,
    *,
    previous_observed_at: str = "",
    previous_water_level_m: str = "",
    water_level_delta_m: str = "",
    seconds_since_previous: str = "",
    consecutive_rising_count: str = "0",
    consecutive_falling_count: str = "0",
    trend_rule_v1: str = "stable",
) -> dict[str, str]:
    return {
        "station_code": station_code,
        "station_name": station_name,
        "observed_at": observed_at,
        "water_level_m": water_level_m,
        "previous_observed_at": previous_observed_at,
        "previous_water_level_m": previous_water_level_m,
        "water_level_delta_m": water_level_delta_m,
        "seconds_since_previous": seconds_since_previous,
        "consecutive_rising_count": consecutive_rising_count,
        "consecutive_falling_count": consecutive_falling_count,
        "trend_rule_v1": trend_rule_v1,
    }


class BuildFloodWaterLevelAnomaliesDay14Test(unittest.TestCase):
    def test_builds_anomaly_records_trend_labels_and_quality_summary(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            features_path = root / "features.csv"
            day13_quality_path = root / "day13_quality.json"
            anomalies_path = root / "anomalies.csv"
            trends_path = root / "trends.csv"
            quality_path = root / "quality.json"

            write_feature_rows(
                features_path,
                [
                    feature_row("ST001", "重复站", "2026-01-01 00:00:00", "0.1"),
                    feature_row(
                        "ST001",
                        "重复站",
                        "2026-01-01 00:00:00",
                        "0.12",
                        previous_observed_at="2026-01-01 00:00:00",
                        previous_water_level_m="0.1",
                        water_level_delta_m="0.02",
                        seconds_since_previous="0",
                    ),
                    feature_row("ST002", "断档站", "2026-01-01 00:00:00", "0.1"),
                    feature_row(
                        "ST002",
                        "断档站",
                        "2026-01-01 07:00:01",
                        "0.11",
                        previous_observed_at="2026-01-01 00:00:00",
                        previous_water_level_m="0.1",
                        water_level_delta_m="0.01",
                        seconds_since_previous="25201",
                    ),
                    feature_row("ST003", "跳变站", "2026-01-01 00:00:00", "0.1"),
                    feature_row(
                        "ST003",
                        "跳变站",
                        "2026-01-01 00:05:00",
                        "0.35",
                        previous_observed_at="2026-01-01 00:00:00",
                        previous_water_level_m="0.1",
                        water_level_delta_m="0.25",
                        seconds_since_previous="300",
                        consecutive_rising_count="1",
                        trend_rule_v1="rising",
                    ),
                    feature_row("ST004", "尖峰站", "2026-01-01 00:00:00", "0.1"),
                    feature_row(
                        "ST004",
                        "尖峰站",
                        "2026-01-01 00:05:00",
                        "0.4",
                        previous_observed_at="2026-01-01 00:00:00",
                        previous_water_level_m="0.1",
                        water_level_delta_m="0.3",
                        seconds_since_previous="300",
                        consecutive_rising_count="1",
                        trend_rule_v1="rising",
                    ),
                    feature_row(
                        "ST004",
                        "尖峰站",
                        "2026-01-01 00:10:00",
                        "0.11",
                        previous_observed_at="2026-01-01 00:05:00",
                        previous_water_level_m="0.4",
                        water_level_delta_m="-0.29",
                        seconds_since_previous="300",
                        consecutive_falling_count="1",
                        trend_rule_v1="fluctuating",
                    ),
                    feature_row("ST005", "持续上升站", "2026-01-01 00:00:00", "0.1"),
                    feature_row(
                        "ST005",
                        "持续上升站",
                        "2026-01-01 00:05:00",
                        "0.12",
                        previous_observed_at="2026-01-01 00:00:00",
                        previous_water_level_m="0.1",
                        water_level_delta_m="0.02",
                        seconds_since_previous="300",
                        consecutive_rising_count="1",
                        trend_rule_v1="stable",
                    ),
                    feature_row(
                        "ST005",
                        "持续上升站",
                        "2026-01-01 00:10:00",
                        "0.14",
                        previous_observed_at="2026-01-01 00:05:00",
                        previous_water_level_m="0.12",
                        water_level_delta_m="0.02",
                        seconds_since_previous="300",
                        consecutive_rising_count="2",
                        trend_rule_v1="rising",
                    ),
                    feature_row("ST006", "快速下降站", "2026-01-01 00:00:00", "0.4"),
                    feature_row(
                        "ST006",
                        "快速下降站",
                        "2026-01-01 00:05:00",
                        "0.15",
                        previous_observed_at="2026-01-01 00:00:00",
                        previous_water_level_m="0.4",
                        water_level_delta_m="-0.25",
                        seconds_since_previous="300",
                        consecutive_falling_count="1",
                        trend_rule_v1="falling",
                    ),
                    feature_row("ST007", "数据不足站", "2026-01-01 00:00:00", "0.2"),
                    feature_row("ST008", "稳定站", "2026-01-01 00:00:00", "0.1"),
                    feature_row(
                        "ST008",
                        "稳定站",
                        "2026-01-01 00:05:00",
                        "0.105",
                        previous_observed_at="2026-01-01 00:00:00",
                        previous_water_level_m="0.1",
                        water_level_delta_m="0.005",
                        seconds_since_previous="300",
                        trend_rule_v1="stable",
                    ),
                ],
            )
            day13_quality_path.write_text(
                json.dumps({"total_records": 17, "station_count": 8}, ensure_ascii=False),
                encoding="utf-8",
            )

            quality = day14.build_day14_outputs(
                features_path=features_path,
                day13_quality_path=day13_quality_path,
                anomalies_output_path=anomalies_path,
                trends_output_path=trends_path,
                quality_output_path=quality_path,
            )

            with anomalies_path.open("r", encoding="utf-8-sig") as file:
                anomalies = list(csv.DictReader(file))
            anomaly_types = [row["anomaly_type"] for row in anomalies]
            self.assertIn("duplicate_or_non_positive_interval", anomaly_types)
            self.assertIn("stale_gap", anomaly_types)
            self.assertIn("instant_jump_candidate", anomaly_types)
            self.assertIn("short_spike_candidate", anomaly_types)

            duplicate = next(
                row
                for row in anomalies
                if row["anomaly_type"] == "duplicate_or_non_positive_interval"
            )
            self.assertEqual(duplicate["station_code"], "ST001")
            self.assertEqual(duplicate["seconds_since_previous"], "0")
            self.assertEqual(duplicate["severity"], "high")
            self.assertIn("非正时间差", duplicate["anomaly_description"])

            stale = next(row for row in anomalies if row["anomaly_type"] == "stale_gap")
            self.assertEqual(stale["station_code"], "ST002")
            self.assertEqual(stale["severity"], "medium")
            self.assertIn("长时间未更新", stale["anomaly_description"])

            spike = next(
                row for row in anomalies if row["anomaly_type"] == "short_spike_candidate"
            )
            self.assertEqual(spike["station_code"], "ST004")
            self.assertEqual(spike["observed_at"], "2026-01-01 00:05:00")
            self.assertEqual(spike["water_level_delta_m"], "0.3")
            self.assertEqual(spike["recovery_observed_at"], "2026-01-01 00:10:00")
            self.assertEqual(spike["recovery_delta_m"], "-0.29")
            self.assertEqual(spike["severity"], "high")

            with trends_path.open("r", encoding="utf-8-sig") as file:
                trends = list(csv.DictReader(file))
            labels_by_station_time = {
                (row["station_code"], row["observed_at"]): row["enhanced_trend_label"]
                for row in trends
            }
            self.assertEqual(
                labels_by_station_time[("ST001", "2026-01-01 00:00:00")],
                "data_insufficient",
            )
            self.assertEqual(
                labels_by_station_time[("ST002", "2026-01-01 07:00:01")],
                "long_gap",
            )
            self.assertEqual(
                labels_by_station_time[("ST003", "2026-01-01 00:05:00")],
                "rapid_rising",
            )
            self.assertEqual(
                labels_by_station_time[("ST004", "2026-01-01 00:05:00")],
                "short_spike",
            )
            self.assertEqual(
                labels_by_station_time[("ST005", "2026-01-01 00:10:00")],
                "sustained_rising",
            )
            self.assertEqual(
                labels_by_station_time[("ST006", "2026-01-01 00:05:00")],
                "rapid_falling",
            )
            self.assertEqual(
                labels_by_station_time[("ST008", "2026-01-01 00:05:00")],
                "stable",
            )

            self.assertEqual(quality["total_anomaly_count"], len(anomalies))
            self.assertEqual(quality["affected_station_count"], 5)
            self.assertEqual(
                quality["anomaly_type_counts"]["duplicate_or_non_positive_interval"],
                1,
            )
            self.assertEqual(quality["anomaly_type_counts"]["stale_gap"], 1)
            self.assertEqual(quality["anomaly_type_counts"]["short_spike_candidate"], 1)
            self.assertEqual(quality["trend_label_counts"]["short_spike"], 1)
            self.assertEqual(quality["trend_label_counts"]["long_gap"], 1)
            self.assertEqual(quality["source_day13_quality"]["total_records"], 17)
            self.assertEqual(
                quality["thresholds"]["abnormal_interval_seconds"],
                day14.ABNORMAL_INTERVAL_SECONDS,
            )
            self.assertTrue(quality["high_risk_examples"])

            persisted_quality = json.loads(quality_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted_quality, quality)


if __name__ == "__main__":
    unittest.main()
