from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


RULE_VERSION = "flood_rule_v1"
RULE_DESCRIPTION = (
    "风险等级基于最新积涝点水位统一阈值；趋势基于最近6条有效积涝水位序列。"
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def assess_risk_level(water_level_m: float | None) -> str:
    if water_level_m is None:
        return "no_data"
    if water_level_m < 0.15:
        return "normal"
    if water_level_m < 0.30:
        return "attention"
    if water_level_m < 0.50:
        return "warning"
    return "danger"


def assess_trend(water_levels: list[float]) -> str:
    if not water_levels:
        return "no_data"
    if len(water_levels) == 1:
        return "stable"

    level_range = max(water_levels) - min(water_levels)
    if level_range <= 0.02:
        return "stable"

    adjacent_pairs = zip(water_levels, water_levels[1:])
    deltas = [current - previous for previous, current in adjacent_pairs]
    if all(delta > 0 for delta in deltas):
        return "rising"
    if all(delta < 0 for delta in deltas):
        return "falling"
    return "fluctuating"


def build_assessment(
    *,
    station: dict[str, Any],
    recent_levels: list[dict[str, Any]],
    generated_at: str | None = None,
) -> dict[str, Any]:
    latest = recent_levels[-1] if recent_levels else None
    latest_water_level = latest["water_level_m"] if latest is not None else None
    water_levels = [
        row["water_level_m"]
        for row in recent_levels
        if row["water_level_m"] is not None
    ]

    return {
        "station_code": station["station_code"],
        "station_name": station["station_name"],
        "latest_observed_at": latest["observed_at"] if latest is not None else None,
        "latest_water_level_m": latest_water_level,
        "risk_level": assess_risk_level(latest_water_level),
        "trend": assess_trend(water_levels),
        "rule_version": RULE_VERSION,
        "rule_description": RULE_DESCRIPTION,
        "generated_at": generated_at or utc_now_iso(),
    }
