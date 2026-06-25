from __future__ import annotations

from fastapi import FastAPI

from backend.app.api.routes import create_api_router
from backend.app.core.config import Settings
from backend.app.repositories.water_repository import WaterRepository


settings = Settings.from_environment()
repository = WaterRepository(settings)

app = FastAPI(title="Shenzhen Flood Monitoring API")
app.include_router(create_api_router(repository), prefix="/api")


@app.get("/health")
def health_check() -> dict[str, object]:
    return {
        "status": "ok",
        "database": {
            "status": "ok",
            "path": str(settings.database_path),
            "tables": repository.get_table_names(),
        },
    }
