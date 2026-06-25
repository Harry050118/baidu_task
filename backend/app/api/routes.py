from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query

from backend.app.repositories.water_repository import WaterRepository


def create_api_router(repository: WaterRepository) -> APIRouter:
    router = APIRouter()

    @router.get("/map/points")
    def get_map_points() -> dict[str, list[dict[str, Any]]]:
        points = [
            {
                "station_code": row["station_code"],
                "station_name": row["station_name"],
                "station_type": row["station_type"],
                "latest_observed_at": row["observed_at"],
                "latest_water_level_m": row["water_level_m"],
                "raw_water_level": row["raw_water_level"],
                "has_coordinates": False,
                "coordinate_status": "missing_coordinates",
            }
            for row in repository.get_latest_flood_water_levels()
        ]
        return {"points": points}

    @router.get("/points/{station_code}")
    def get_point_detail(station_code: str) -> dict[str, Any]:
        station = _get_flood_station_or_404(repository, station_code)
        latest = repository.get_latest_flood_water_level(station_code)
        if latest is None:
            raise HTTPException(status_code=404, detail="flood station not found")

        return {
            "station": station,
            "latest_water_level": {
                "latest_observed_at": latest["observed_at"],
                "latest_water_level_m": latest["water_level_m"],
                "raw_water_level": latest["raw_water_level"],
            },
            "coordinates": {
                "has_coordinates": False,
                "coordinate_status": "missing_coordinates",
            },
        }

    @router.get("/points/{station_code}/history")
    def get_point_history(
        station_code: str,
        limit: Annotated[int, Query(ge=1, le=5000)] = 500,
    ) -> dict[str, Any]:
        station = _get_flood_station_or_404(repository, station_code)
        return {
            "station": station,
            "items": repository.get_flood_water_level_history(
                station_code=station_code,
                limit=limit,
            ),
        }

    @router.get("/data/time-range")
    def get_data_time_range() -> dict[str, dict[str, Any]]:
        return repository.get_data_time_ranges()

    @router.get("/stats/overview")
    def get_stats_overview() -> dict[str, Any]:
        return repository.get_stats_overview()

    @router.get("/status/data")
    def get_data_status() -> dict[str, Any]:
        return repository.get_data_status()

    @router.get("/imports/latest")
    def get_latest_import_batch() -> dict[str, Any]:
        return repository.get_latest_import_batch()

    return router


def _get_flood_station_or_404(
    repository: WaterRepository,
    station_code: str,
) -> dict[str, Any]:
    station = repository.get_flood_station(station_code)
    if station is None:
        raise HTTPException(status_code=404, detail="flood station not found")
    return station
