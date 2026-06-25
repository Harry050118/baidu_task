from __future__ import annotations

import sqlite3
from typing import Any

from backend.app.core.config import Settings
from backend.app.core.database import connect_readonly


class WaterRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _scalar(self, conn: sqlite3.Connection, sql: str) -> Any:
        return conn.execute(sql).fetchone()[0]

    def get_table_names(self) -> list[str]:
        with connect_readonly(self.settings) as conn:
            return [
                row["name"]
                for row in conn.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table'
                        AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                    """
                )
            ]

    def get_database_summary(self) -> dict[str, dict[str, Any]]:
        with connect_readonly(self.settings) as conn:
            flood_matched = self._scalar(
                conn,
                """
                SELECT COUNT(DISTINCT f.station_code)
                FROM flood_water_levels AS f
                INNER JOIN stations AS s ON s.station_code = f.station_code
                """,
            )
            flood_missing = self._scalar(
                conn,
                """
                SELECT COUNT(DISTINCT f.station_code)
                FROM flood_water_levels AS f
                LEFT JOIN stations AS s ON s.station_code = f.station_code
                WHERE s.station_code IS NULL
                """,
            )
            reservoir_missing = self._scalar(
                conn,
                """
                SELECT COUNT(DISTINCT r.station_code)
                FROM reservoir_water_levels AS r
                LEFT JOIN stations AS s ON s.station_code = r.station_code
                WHERE s.station_code IS NULL
                """,
            )

            return {
                "stations": {
                    "rows": self._scalar(conn, "SELECT COUNT(*) FROM stations"),
                },
                "flood_water_levels": {
                    "rows": self._scalar(conn, "SELECT COUNT(*) FROM flood_water_levels"),
                    "unique_station_codes": self._scalar(
                        conn,
                        "SELECT COUNT(DISTINCT station_code) FROM flood_water_levels",
                    ),
                    "matched_station_codes": flood_matched,
                    "missing_station_codes": flood_missing,
                    "observed_at_min": self._scalar(
                        conn,
                        "SELECT MIN(observed_at) FROM flood_water_levels",
                    ),
                    "observed_at_max": self._scalar(
                        conn,
                        "SELECT MAX(observed_at) FROM flood_water_levels",
                    ),
                },
                "reservoir_water_levels": {
                    "rows": self._scalar(conn, "SELECT COUNT(*) FROM reservoir_water_levels"),
                    "unique_station_codes": self._scalar(
                        conn,
                        "SELECT COUNT(DISTINCT station_code) FROM reservoir_water_levels",
                    ),
                    "null_water_level_rows": self._scalar(
                        conn,
                        """
                        SELECT COUNT(*)
                        FROM reservoir_water_levels
                        WHERE water_level_m IS NULL
                        """,
                    ),
                    "missing_station_codes": reservoir_missing,
                },
            }

    def get_latest_flood_water_levels(self, limit: int = 148) -> list[dict[str, Any]]:
        with connect_readonly(self.settings) as conn:
            rows = conn.execute(
                """
                WITH ranked AS (
                    SELECT
                        f.station_code,
                        f.observed_at,
                        f.water_level_m,
                        f.raw_water_level,
                        ROW_NUMBER() OVER (
                            PARTITION BY f.station_code
                            ORDER BY f.observed_at DESC, f.id DESC
                        ) AS row_number
                    FROM flood_water_levels AS f
                )
                SELECT
                    ranked.station_code,
                    s.station_name,
                    s.station_type,
                    ranked.observed_at,
                    ranked.water_level_m,
                    ranked.raw_water_level
                FROM ranked
                INNER JOIN stations AS s ON s.station_code = ranked.station_code
                WHERE ranked.row_number = 1
                ORDER BY ranked.observed_at DESC, ranked.station_code
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_flood_station(self, station_code: str) -> dict[str, Any] | None:
        with connect_readonly(self.settings) as conn:
            row = conn.execute(
                """
                SELECT s.station_code, s.station_name, s.station_type
                FROM stations AS s
                WHERE s.station_code = ?
                    AND EXISTS (
                        SELECT 1
                        FROM flood_water_levels AS f
                        WHERE f.station_code = s.station_code
                    )
                """,
                (station_code,),
            ).fetchone()
        return dict(row) if row is not None else None

    def get_latest_flood_water_level(self, station_code: str) -> dict[str, Any] | None:
        with connect_readonly(self.settings) as conn:
            row = conn.execute(
                """
                SELECT station_code, observed_at, water_level_m, raw_water_level
                FROM flood_water_levels
                WHERE station_code = ?
                ORDER BY observed_at DESC, id DESC
                LIMIT 1
                """,
                (station_code,),
            ).fetchone()
        return dict(row) if row is not None else None

    def get_flood_water_level_history(
        self,
        station_code: str,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        with connect_readonly(self.settings) as conn:
            rows = conn.execute(
                """
                SELECT id, station_code, observed_at, water_level_m, raw_water_level
                FROM flood_water_levels
                WHERE station_code = ?
                ORDER BY observed_at DESC, id DESC
                LIMIT ?
                """,
                (station_code, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_data_time_ranges(self) -> dict[str, dict[str, Any]]:
        summary = self.get_database_summary()
        return {
            "flood_water_levels": {
                "observed_at_min": summary["flood_water_levels"]["observed_at_min"],
                "observed_at_max": summary["flood_water_levels"]["observed_at_max"],
            },
            "reservoir_water_levels": {
                "quality_role": "status_summary_only",
                "rows": summary["reservoir_water_levels"]["rows"],
                "null_water_level_rows": summary["reservoir_water_levels"][
                    "null_water_level_rows"
                ],
            },
        }

    def get_station_coordinate_status(self) -> dict[str, Any]:
        with connect_readonly(self.settings) as conn:
            columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(stations)").fetchall()
            }
            total_stations = self._scalar(conn, "SELECT COUNT(*) FROM stations")

        coordinate_columns = {"longitude", "latitude", "coord_source", "coord_quality"}
        has_coordinate_columns = coordinate_columns.issubset(columns)
        return {
            "status": "available" if has_coordinate_columns else "missing_coordinates",
            "has_coordinate_columns": has_coordinate_columns,
            "total_stations": total_stations,
            "missing_coordinate_stations": 0 if has_coordinate_columns else total_stations,
            "required_action": "coordinate_source_and_manual_review_required",
        }
