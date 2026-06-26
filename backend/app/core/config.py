from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATABASE_URL = "sqlite:///data/local/shenzhen_water.db"


def _load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


@dataclass(frozen=True)
class Settings:
    database_url: str = DEFAULT_DATABASE_URL
    app_env: str = "local"
    project_root: Path = PROJECT_ROOT
    amap_web_service_key: str = ""

    @classmethod
    def from_environment(cls, env_file: Path | None = None) -> "Settings":
        env_values = _load_env_file(env_file or PROJECT_ROOT / ".env")
        return cls(
            database_url=os.environ.get(
                "DATABASE_URL",
                env_values.get("DATABASE_URL", DEFAULT_DATABASE_URL),
            ),
            app_env=os.environ.get("APP_ENV", env_values.get("APP_ENV", "local")),
            amap_web_service_key=os.environ.get(
                "AMAP_WEB_SERVICE_KEY",
                env_values.get("AMAP_WEB_SERVICE_KEY", ""),
            ),
        )

    @property
    def database_path(self) -> Path:
        prefix = "sqlite:///"
        if not self.database_url.startswith(prefix):
            raise ValueError("Only sqlite:/// DATABASE_URL values are supported")

        raw_path = unquote(self.database_url[len(prefix) :])
        path = Path(raw_path)
        if not path.is_absolute():
            path = self.project_root / path
        return path.resolve()
