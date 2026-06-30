#!/usr/bin/env python3
"""Build Day 14 anomaly and enhanced-trend outputs from Day 13 features."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_FEATURES = PROJECT_ROOT / "data" / "features" / "flood_water_level_features_day13.csv"
DEFAULT_DAY13_QUALITY = (
    PROJECT_ROOT / "data" / "features" / "flood_water_level_features_day13_quality.json"
)
DEFAULT_ANOMALIES_OUTPUT = (
    PROJECT_ROOT / "data" / "features" / "flood_water_level_anomalies_day14.csv"
)
DEFAULT_TRENDS_OUTPUT = (
    PROJECT_ROOT / "data" / "features" / "flood_water_level_trends_day14.csv"
)
DEFAULT_QUALITY_OUTPUT = (
    PROJECT_ROOT / "data" / "features" / "flood_water_level_anomalies_day14_quality.json"
)

ABNORMAL_INTERVAL_SECONDS = 21_600
INSTANT_JUMP_DELTA_M = 0.20
INSTANT_JUMP_MAX_SECONDS = 3_600
SUSTAINED_TREND_COUNT = 2

ANOMALY_FIELDNAMES = [
    "station_code",
    "station_name",
    "observed_at",
    "water_level_m",
    "previous_observed_at",
    "previous_water_level_m",
    "water_level_delta_m",
    "seconds_since_previous",
    "anomaly_type",
    "severity",
    "anomaly_description",
    "recovery_observed_at",
    "recovery_water_level_m",
    "recovery_delta_m",
    "recovery_seconds",
]

TREND_FIELDNAMES = [
    "station_code",
    "station_name",
    "observed_at",
    "water_level_m",
    "previous_observed_at",
    "previous_water_level_m",
    "water_level_delta_m",
    "seconds_since_previous",
    "consecutive_rising_count",
    "consecutive_falling_count",
    "trend_rule_v1",
    "enhanced_trend_label",
    "enhanced_trend_description",
]

LIMITATIONS = [
    "当前无降雨特征，无法提前感知尚未体现在水位序列中的降雨冲击。",
    "Day 14 只整理异常候选和趋势解释，不训练机器学习模型。",
    "Day 14 不接预测接口，不改前端主流程。",
    "异常记录是离线数据质量与趋势候选结果，不等同于业务告警。",
]


@dataclass
class FeatureRow:
    station_code: str
    station_name: str
    observed_at: str
    water_level_m: str
    previous_observed_at: str
    previous_water_level_m: str
    water_level_delta_m: str
    seconds_since_previous: str
    consecutive_rising_count: str
    consecutive_falling_count: str
    trend_rule_v1: str
    water_level_value: float | None
    delta_value: float | None
    seconds_value: int | None
    rising_count_value: int
    falling_count_value: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Day 14 flood water-level anomalies, enhanced trends, and quality JSON."
    )
    parser.add_argument("--features", type=Path, default=DEFAULT_FEATURES)
    parser.add_argument("--day13-quality", type=Path, default=DEFAULT_DAY13_QUALITY)
    parser.add_argument("--anomalies-output", type=Path, default=DEFAULT_ANOMALIES_OUTPUT)
    parser.add_argument("--trends-output", type=Path, default=DEFAULT_TRENDS_OUTPUT)
    parser.add_argument("--quality-output", type=Path, default=DEFAULT_QUALITY_OUTPUT)
    return parser.parse_args()


def parse_optional_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def parse_optional_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    return int(float(value))


def parse_int(value: str | None) -> int:
    if value is None or value == "":
        return 0
    return int(float(value))


def read_feature_row(row: dict[str, str]) -> FeatureRow:
    water_level = row.get("water_level_m", "")
    delta = row.get("water_level_delta_m", "")
    seconds = row.get("seconds_since_previous", "")
    rising_count = row.get("consecutive_rising_count", "0")
    falling_count = row.get("consecutive_falling_count", "0")
    return FeatureRow(
        station_code=row.get("station_code", ""),
        station_name=row.get("station_name", ""),
        observed_at=row.get("observed_at", ""),
        water_level_m=water_level,
        previous_observed_at=row.get("previous_observed_at", ""),
        previous_water_level_m=row.get("previous_water_level_m", ""),
        water_level_delta_m=delta,
        seconds_since_previous=seconds,
        consecutive_rising_count=rising_count,
        consecutive_falling_count=falling_count,
        trend_rule_v1=row.get("trend_rule_v1", ""),
        water_level_value=parse_optional_float(water_level),
        delta_value=parse_optional_float(delta),
        seconds_value=parse_optional_int(seconds),
        rising_count_value=parse_int(rising_count),
        falling_count_value=parse_int(falling_count),
    )


def is_instant_jump(row: FeatureRow) -> bool:
    return (
        row.delta_value is not None
        and row.seconds_value is not None
        and abs(row.delta_value) >= INSTANT_JUMP_DELTA_M
        and 0 < row.seconds_value <= INSTANT_JUMP_MAX_SECONDS
    )


def is_stale_gap(row: FeatureRow) -> bool:
    return row.seconds_value is not None and row.seconds_value > ABNORMAL_INTERVAL_SECONDS


def is_duplicate_or_non_positive(row: FeatureRow) -> bool:
    return row.seconds_value is not None and row.seconds_value <= 0


def is_short_spike(peak: FeatureRow, recovery: FeatureRow) -> bool:
    return (
        peak.station_code == recovery.station_code
        and peak.delta_value is not None
        and recovery.delta_value is not None
        and peak.seconds_value is not None
        and recovery.seconds_value is not None
        and peak.delta_value >= INSTANT_JUMP_DELTA_M
        and recovery.delta_value <= -INSTANT_JUMP_DELTA_M
        and 0 < peak.seconds_value <= INSTANT_JUMP_MAX_SECONDS
        and 0 < recovery.seconds_value <= INSTANT_JUMP_MAX_SECONDS
    )


def build_base_anomaly(
    row: FeatureRow,
    *,
    anomaly_type: str,
    severity: str,
    description: str,
) -> dict[str, str]:
    return {
        "station_code": row.station_code,
        "station_name": row.station_name,
        "observed_at": row.observed_at,
        "water_level_m": row.water_level_m,
        "previous_observed_at": row.previous_observed_at,
        "previous_water_level_m": row.previous_water_level_m,
        "water_level_delta_m": row.water_level_delta_m,
        "seconds_since_previous": row.seconds_since_previous,
        "anomaly_type": anomaly_type,
        "severity": severity,
        "anomaly_description": description,
        "recovery_observed_at": "",
        "recovery_water_level_m": "",
        "recovery_delta_m": "",
        "recovery_seconds": "",
    }


def detect_row_anomalies(row: FeatureRow) -> list[dict[str, str]]:
    anomalies: list[dict[str, str]] = []
    if is_duplicate_or_non_positive(row):
        anomalies.append(
            build_base_anomaly(
                row,
                anomaly_type="duplicate_or_non_positive_interval",
                severity="high",
                description=(
                    f"同站点上一条观测到当前观测的秒差为 {row.seconds_since_previous}，"
                    "属于重复时间或非正时间差。"
                ),
            )
        )
    if is_stale_gap(row):
        anomalies.append(
            build_base_anomaly(
                row,
                anomaly_type="stale_gap",
                severity="medium",
                description=(
                    f"距上一条有效观测 {row.seconds_since_previous} 秒，"
                    f"超过长时间未更新阈值 {ABNORMAL_INTERVAL_SECONDS} 秒。"
                ),
            )
        )
    if is_instant_jump(row):
        direction = "上升" if row.delta_value is not None and row.delta_value > 0 else "下降"
        anomalies.append(
            build_base_anomaly(
                row,
                anomaly_type="instant_jump_candidate",
                severity="high",
                description=(
                    f"短时间内水位{direction} {row.water_level_delta_m}m，"
                    f"秒差 {row.seconds_since_previous}，属于瞬时跳变候选。"
                ),
            )
        )
    return anomalies


def build_spike_anomaly(peak: FeatureRow, recovery: FeatureRow) -> dict[str, str]:
    anomaly = build_base_anomaly(
        peak,
        anomaly_type="short_spike_candidate",
        severity="high",
        description=(
            f"水位先在 {peak.seconds_since_previous} 秒内上升 {peak.water_level_delta_m}m，"
            f"随后在 {recovery.seconds_since_previous} 秒内回落 {recovery.water_level_delta_m}m，"
            "属于短时尖峰候选。"
        ),
    )
    anomaly.update(
        {
            "recovery_observed_at": recovery.observed_at,
            "recovery_water_level_m": recovery.water_level_m,
            "recovery_delta_m": recovery.water_level_delta_m,
            "recovery_seconds": recovery.seconds_since_previous,
        }
    )
    return anomaly


def enhanced_trend_for_row(row: FeatureRow, *, short_spike: bool) -> tuple[str, str]:
    if short_spike:
        return "short_spike", "短时间大幅升高后又快速回落，标记为短时尖峰。"
    if is_stale_gap(row):
        return (
            "long_gap",
            f"距上一条有效观测 {row.seconds_since_previous} 秒，超过 {ABNORMAL_INTERVAL_SECONDS} 秒。",
        )
    if is_duplicate_or_non_positive(row):
        return "data_insufficient", "观测秒差为非正值，无法解释为有效水位趋势。"
    if row.seconds_value is None or row.delta_value is None:
        return "data_insufficient", "缺少上一条有效观测或变化量，暂不足以判断增强趋势。"
    if (
        row.delta_value >= INSTANT_JUMP_DELTA_M
        and 0 < row.seconds_value <= INSTANT_JUMP_MAX_SECONDS
    ):
        return "rapid_rising", "短时间内水位快速上升。"
    if (
        row.delta_value <= -INSTANT_JUMP_DELTA_M
        and 0 < row.seconds_value <= INSTANT_JUMP_MAX_SECONDS
    ):
        return "rapid_falling", "短时间内水位快速下降。"
    if row.rising_count_value >= SUSTAINED_TREND_COUNT:
        return "sustained_rising", "同站点水位已连续上升。"
    if row.falling_count_value >= SUSTAINED_TREND_COUNT:
        return "sustained_falling", "同站点水位已连续下降。"
    if row.trend_rule_v1 == "fluctuating":
        return "fluctuating", "最近有效水位序列呈波动态势。"
    return "stable", "水位变化幅度较小或规则趋势为稳定。"


def build_trend_row(row: FeatureRow, *, short_spike: bool) -> dict[str, str]:
    label, description = enhanced_trend_for_row(row, short_spike=short_spike)
    return {
        "station_code": row.station_code,
        "station_name": row.station_name,
        "observed_at": row.observed_at,
        "water_level_m": row.water_level_m,
        "previous_observed_at": row.previous_observed_at,
        "previous_water_level_m": row.previous_water_level_m,
        "water_level_delta_m": row.water_level_delta_m,
        "seconds_since_previous": row.seconds_since_previous,
        "consecutive_rising_count": row.consecutive_rising_count,
        "consecutive_falling_count": row.consecutive_falling_count,
        "trend_rule_v1": row.trend_rule_v1,
        "enhanced_trend_label": label,
        "enhanced_trend_description": description,
    }


def load_day13_quality(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Day 13 quality JSON does not exist: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_input_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"Day 13 feature CSV does not exist: {path}. "
            "Run scripts/build_flood_water_level_features.py first."
        )


def build_day14_outputs(
    *,
    features_path: Path,
    day13_quality_path: Path,
    anomalies_output_path: Path,
    trends_output_path: Path,
    quality_output_path: Path,
) -> dict[str, Any]:
    ensure_input_exists(features_path)
    day13_quality = load_day13_quality(day13_quality_path)

    anomalies_output_path.parent.mkdir(parents=True, exist_ok=True)
    trends_output_path.parent.mkdir(parents=True, exist_ok=True)
    quality_output_path.parent.mkdir(parents=True, exist_ok=True)

    anomaly_type_counts: Counter[str] = Counter()
    severity_counts: Counter[str] = Counter()
    station_anomaly_counts: Counter[str] = Counter()
    trend_label_counts: Counter[str] = Counter()
    high_risk_examples: list[dict[str, str]] = []
    total_anomaly_count = 0

    pending_row: FeatureRow | None = None

    def write_anomaly(writer: csv.DictWriter, anomaly: dict[str, str]) -> None:
        nonlocal total_anomaly_count
        writer.writerow(anomaly)
        total_anomaly_count += 1
        anomaly_type_counts[anomaly["anomaly_type"]] += 1
        severity_counts[anomaly["severity"]] += 1
        station_anomaly_counts[anomaly["station_code"]] += 1
        if anomaly["severity"] == "high" and len(high_risk_examples) < 10:
            high_risk_examples.append(anomaly)

    def flush_pending_trend(writer: csv.DictWriter, *, short_spike: bool = False) -> None:
        nonlocal pending_row
        if pending_row is None:
            return
        trend_row = build_trend_row(pending_row, short_spike=short_spike)
        writer.writerow(trend_row)
        trend_label_counts[trend_row["enhanced_trend_label"]] += 1
        pending_row = None

    with (
        features_path.open("r", encoding="utf-8-sig", newline="") as features_file,
        anomalies_output_path.open("w", encoding="utf-8-sig", newline="") as anomalies_file,
        trends_output_path.open("w", encoding="utf-8-sig", newline="") as trends_file,
    ):
        reader = csv.DictReader(features_file)
        anomaly_writer = csv.DictWriter(anomalies_file, fieldnames=ANOMALY_FIELDNAMES)
        trend_writer = csv.DictWriter(trends_file, fieldnames=TREND_FIELDNAMES)
        anomaly_writer.writeheader()
        trend_writer.writeheader()

        for raw_row in reader:
            current_row = read_feature_row(raw_row)
            current_starts_new_station = (
                pending_row is not None
                and pending_row.station_code != current_row.station_code
            )
            if current_starts_new_station:
                flush_pending_trend(trend_writer)

            if pending_row is not None and is_short_spike(pending_row, current_row):
                write_anomaly(anomaly_writer, build_spike_anomaly(pending_row, current_row))
                flush_pending_trend(trend_writer, short_spike=True)
            else:
                flush_pending_trend(trend_writer)

            for anomaly in detect_row_anomalies(current_row):
                write_anomaly(anomaly_writer, anomaly)

            pending_row = current_row

        flush_pending_trend(trend_writer)

    quality = {
        "anomaly_file": str(anomalies_output_path),
        "trend_file": str(trends_output_path),
        "total_anomaly_count": total_anomaly_count,
        "affected_station_count": len(station_anomaly_counts),
        "anomaly_type_counts": dict(sorted(anomaly_type_counts.items())),
        "severity_counts": dict(sorted(severity_counts.items())),
        "high_risk_examples": high_risk_examples,
        "station_anomaly_counts": dict(
            sorted(station_anomaly_counts.items(), key=lambda item: (-item[1], item[0]))
        ),
        "trend_label_counts": dict(sorted(trend_label_counts.items())),
        "source_day13_quality": day13_quality,
        "thresholds": {
            "abnormal_interval_seconds": ABNORMAL_INTERVAL_SECONDS,
            "instant_jump_delta_m": INSTANT_JUMP_DELTA_M,
            "instant_jump_max_seconds": INSTANT_JUMP_MAX_SECONDS,
            "sustained_trend_count": SUSTAINED_TREND_COUNT,
        },
        "limitations": LIMITATIONS,
    }
    quality_output_path.write_text(
        json.dumps(quality, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return quality


def main() -> None:
    args = parse_args()
    try:
        quality = build_day14_outputs(
            features_path=args.features,
            day13_quality_path=args.day13_quality,
            anomalies_output_path=args.anomalies_output,
            trends_output_path=args.trends_output,
            quality_output_path=args.quality_output,
        )
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    print(f"Generated anomaly CSV: {args.anomalies_output}")
    print(f"Generated enhanced trend CSV: {args.trends_output}")
    print(f"Generated quality summary: {args.quality_output}")
    print(json.dumps(quality, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
