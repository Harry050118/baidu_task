from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.app.repositories.water_repository import WaterRepository
from backend.app.services.assessments import build_assessment, utc_now_iso
from backend.app.services.coordinates.amap_geocoder import (
    AmapGeocoder,
    AmapGeocoderError,
    MissingAmapKeyError,
)


class GeocodeCandidateRequest(BaseModel):
    station_code: str
    address: str | None = None


class ReviewLocationCandidateRequest(BaseModel):
    candidate_id: int
    review_status: Literal["approved", "rejected"]
    review_note: str | None = None


def create_api_router(
    repository: WaterRepository,
    geocoder: Any | None = None,
) -> APIRouter:
    router = APIRouter()
    geocoder = geocoder or AmapGeocoder(repository.settings)

    @router.get("/map/points")
    def get_map_points() -> dict[str, list[dict[str, Any]]]:
        points = []
        for row in repository.get_latest_flood_water_levels():
            point = {
                "station_code": row["station_code"],
                "station_name": row["station_name"],
                "station_type": row["station_type"],
                "latest_observed_at": row["observed_at"],
                "latest_water_level_m": row["water_level_m"],
                "raw_water_level": row["raw_water_level"],
                "has_coordinates": False,
                "coordinate_status": "missing_coordinates",
            }
            if row.get("review_status") == "approved":
                point.update(
                    {
                        "has_coordinates": True,
                        "coordinate_status": "approved",
                        "longitude": row["longitude"],
                        "latitude": row["latitude"],
                        "coord_source": row["coord_source"],
                        "coord_quality": row["coord_quality"],
                        "review_status": row["review_status"],
                    }
                )
            points.append(point)
        return {"points": points}

    @router.get("/points/{station_code}")
    def get_point_detail(station_code: str) -> dict[str, Any]:
        station = _get_flood_station_or_404(repository, station_code)
        latest = repository.get_latest_flood_water_level(station_code)
        if latest is None:
            raise HTTPException(status_code=404, detail="flood station not found")
        approved_location = repository.get_approved_location(station_code)

        coordinates = {
            "has_coordinates": False,
            "coordinate_status": "missing_coordinates",
        }
        if approved_location is not None:
            coordinates = {
                "has_coordinates": True,
                "coordinate_status": "approved",
                "longitude": approved_location["longitude"],
                "latitude": approved_location["latitude"],
                "coord_source": approved_location["coord_source"],
                "coord_quality": approved_location["coord_quality"],
                "review_status": approved_location["review_status"],
            }

        return {
            "station": station,
            "latest_water_level": {
                "latest_observed_at": latest["observed_at"],
                "latest_water_level_m": latest["water_level_m"],
                "raw_water_level": latest["raw_water_level"],
            },
            "coordinates": coordinates,
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

    @router.get("/assessments")
    def get_assessments() -> dict[str, Any]:
        generated_at = utc_now_iso()
        items = []
        for station in repository.get_flood_stations():
            recent_levels = repository.get_recent_flood_water_levels(
                station["station_code"],
            )
            items.append(
                build_assessment(
                    station=station,
                    recent_levels=recent_levels,
                    generated_at=generated_at,
                )
            )
        return {"items": items}

    @router.get("/points/{station_code}/assessment")
    def get_point_assessment(station_code: str) -> dict[str, Any]:
        station = _get_flood_station_or_404(repository, station_code)
        recent_levels = repository.get_recent_flood_water_levels(station_code)
        return build_assessment(station=station, recent_levels=recent_levels)

    @router.get("/stats/overview")
    def get_stats_overview() -> dict[str, Any]:
        return repository.get_stats_overview()

    @router.get("/stats/stations")
    def get_station_type_stats() -> dict[str, Any]:
        return repository.get_station_type_stats()

    @router.get("/status/data")
    def get_data_status() -> dict[str, Any]:
        return repository.get_data_status()

    @router.get("/imports/latest")
    def get_latest_import_batch() -> dict[str, Any]:
        return repository.get_latest_import_batch()

    @router.get("/locations/status")
    def get_locations_status() -> dict[str, Any]:
        return repository.get_location_status()

    @router.post("/locations/geocode-candidates")
    def create_geocode_candidate(
        request: GeocodeCandidateRequest,
    ) -> dict[str, Any]:
        station = repository.get_station(request.station_code)
        if station is None:
            raise HTTPException(status_code=404, detail="station not found")

        address = request.address or f"深圳市{station['station_name']}"
        try:
            amap_payload = geocoder.geocode(address=address, city="深圳")
        except MissingAmapKeyError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except AmapGeocoderError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        geocodes = amap_payload.get("geocodes") or []
        if not geocodes:
            raise HTTPException(status_code=404, detail="geocode candidate not found")

        first = geocodes[0]
        longitude, latitude = _parse_amap_location(first["location"])
        candidate = repository.create_location_candidate(
            station_code=request.station_code,
            longitude=longitude,
            latitude=latitude,
            formatted_address=first.get("formatted_address") or address,
            amap_level=first.get("level"),
            amap_adcode=first.get("adcode"),
        )
        return {
            "station": station,
            "candidate": candidate,
            "amap_status": {
                "status": amap_payload.get("status"),
                "info": amap_payload.get("info"),
                "infocode": amap_payload.get("infocode"),
                "count": amap_payload.get("count"),
            },
        }

    @router.get("/locations/{station_code}/candidates")
    def get_location_candidates(station_code: str) -> dict[str, Any]:
        station = repository.get_station(station_code)
        if station is None:
            raise HTTPException(status_code=404, detail="station not found")
        return {
            "station": station,
            "items": repository.get_location_candidates(station_code),
        }

    @router.post("/locations/{station_code}/review")
    def review_location_candidate(
        station_code: str,
        request: ReviewLocationCandidateRequest,
    ) -> dict[str, Any]:
        station = repository.get_station(station_code)
        if station is None:
            raise HTTPException(status_code=404, detail="station not found")

        candidate = repository.review_location_candidate(
            station_code=station_code,
            candidate_id=request.candidate_id,
            review_status=request.review_status,
            review_note=request.review_note,
        )
        if candidate is None:
            raise HTTPException(status_code=404, detail="location candidate not found")
        return {"station": station, "candidate": candidate}

    return router


def _get_flood_station_or_404(
    repository: WaterRepository,
    station_code: str,
) -> dict[str, Any]:
    station = repository.get_flood_station(station_code)
    if station is None:
        raise HTTPException(status_code=404, detail="flood station not found")
    return station


def _parse_amap_location(location: str) -> tuple[float, float]:
    longitude_text, latitude_text = location.split(",", 1)
    return float(longitude_text), float(latitude_text)
