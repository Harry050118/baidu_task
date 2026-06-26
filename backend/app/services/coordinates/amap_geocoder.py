from __future__ import annotations

from typing import Any

import httpx

from backend.app.core.config import Settings


class MissingAmapKeyError(RuntimeError):
    pass


class AmapGeocoderError(RuntimeError):
    pass


class AmapGeocoder:
    endpoint = "https://restapi.amap.com/v3/geocode/geo"

    def __init__(self, settings: Settings, timeout_seconds: float = 8.0) -> None:
        self.settings = settings
        self.timeout_seconds = timeout_seconds

    def geocode(self, address: str, city: str = "深圳") -> dict[str, Any]:
        key = self.settings.amap_web_service_key.strip()
        if not key:
            raise MissingAmapKeyError("AMAP_WEB_SERVICE_KEY is not configured")

        try:
            response = httpx.get(
                self.endpoint,
                params={
                    "key": key,
                    "address": address,
                    "city": city,
                    "output": "JSON",
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise AmapGeocoderError("amap geocode request failed") from exc
        except ValueError as exc:
            raise AmapGeocoderError("amap geocode response was not valid JSON") from exc

        if str(payload.get("status")) != "1":
            raise AmapGeocoderError(str(payload.get("info") or "amap geocode failed"))
        return payload
