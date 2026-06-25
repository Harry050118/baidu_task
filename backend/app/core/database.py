from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from backend.app.core.config import Settings


def _readonly_uri(path: Path) -> str:
    return f"file:{path.as_posix()}?mode=ro"


@contextmanager
def connect_readonly(settings: Settings) -> Iterator[sqlite3.Connection]:
    database_path = settings.database_path
    if not database_path.exists():
        raise FileNotFoundError(f"Database not found: {database_path}")

    conn = sqlite3.connect(_readonly_uri(database_path), uri=True)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
