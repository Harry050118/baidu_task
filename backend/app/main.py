from __future__ import annotations

import sqlite3

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from backend.app.api.routes import create_api_router
from backend.app.core.config import Settings
from backend.app.repositories.water_repository import WaterRepository
from backend.app.services.coordinates.amap_geocoder import AmapGeocoder


settings = Settings.from_environment()
repository = WaterRepository(settings)
geocoder = AmapGeocoder(settings)


def create_app(
    app_settings: Settings,
    app_repository: WaterRepository | None = None,
    app_geocoder: AmapGeocoder | None = None,
) -> FastAPI:
    app_repository = app_repository or WaterRepository(app_settings)
    app_geocoder = app_geocoder or AmapGeocoder(app_settings)

    app = FastAPI(title="Shenzhen Flood Monitoring API")

    @app.exception_handler(FileNotFoundError)
    @app.exception_handler(sqlite3.Error)
    async def database_unavailable_handler(request, exc) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"detail": "database unavailable"},
        )

    app.include_router(
        create_api_router(app_repository, geocoder=app_geocoder),
        prefix="/api",
    )

    @app.get("/health")
    def health_check() -> dict[str, object]:
        return {
            "status": "ok",
            "database": {
                "status": "ok",
                "path": str(app_settings.database_path),
                "tables": app_repository.get_table_names(),
            },
        }

    return app


app = create_app(settings, repository, geocoder)
