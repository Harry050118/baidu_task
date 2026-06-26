from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

from backend.app.core.config import Settings
from backend.app.core.database import connect_readonly, connect_write


class WaterRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _scalar(self, conn: sqlite3.Connection, sql: str) -> Any:
        return conn.execute(sql).fetchone()[0]

    def _table_exists(self, conn: sqlite3.Connection, table_name: str) -> bool:
        row = conn.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table'
                AND name = ?
            """,
            (table_name,),
        ).fetchone()
        return row is not None

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

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
            if self._table_exists(conn, "location_candidates"):
                rows = conn.execute(
                    """
                    WITH ranked_levels AS (
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
                    ),
                    approved_locations AS (
                        SELECT
                            lc.station_code,
                            lc.longitude,
                            lc.latitude,
                            lc.coord_source,
                            lc.coord_quality,
                            lc.review_status,
                            ROW_NUMBER() OVER (
                                PARTITION BY lc.station_code
                                ORDER BY lc.reviewed_at DESC, lc.updated_at DESC, lc.id DESC
                            ) AS row_number
                        FROM location_candidates AS lc
                        WHERE lc.review_status = 'approved'
                    )
                    SELECT
                        ranked_levels.station_code,
                        s.station_name,
                        s.station_type,
                        ranked_levels.observed_at,
                        ranked_levels.water_level_m,
                        ranked_levels.raw_water_level,
                        approved_locations.longitude,
                        approved_locations.latitude,
                        approved_locations.coord_source,
                        approved_locations.coord_quality,
                        approved_locations.review_status
                    FROM ranked_levels
                    INNER JOIN stations AS s
                        ON s.station_code = ranked_levels.station_code
                    LEFT JOIN approved_locations
                        ON approved_locations.station_code = ranked_levels.station_code
                        AND approved_locations.row_number = 1
                    WHERE ranked_levels.row_number = 1
                    ORDER BY ranked_levels.observed_at DESC, ranked_levels.station_code
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
                return [dict(row) for row in rows]

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

    def get_station(self, station_code: str) -> dict[str, Any] | None:
        with connect_readonly(self.settings) as conn:
            row = conn.execute(
                """
                SELECT station_code, station_name, station_type
                FROM stations
                WHERE station_code = ?
                """,
                (station_code,),
            ).fetchone()
        return dict(row) if row is not None else None

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

    def get_stats_overview(self) -> dict[str, Any]:
        summary = self.get_database_summary()
        coordinate_status = self.get_station_coordinate_status()
        return {
            "flood_station_count": summary["flood_water_levels"][
                "unique_station_codes"
            ],
            "latest_observed_at": summary["flood_water_levels"]["observed_at_max"],
            "flood_record_count": summary["flood_water_levels"]["rows"],
            "stations_total": summary["stations"]["rows"],
            "coordinate_status": coordinate_status["status"],
            "has_coordinates": coordinate_status["has_coordinate_columns"],
        }

    def get_station_type_stats(self) -> dict[str, Any]:
        with connect_readonly(self.settings) as conn:
            rows = conn.execute(
                """
                SELECT station_type, COUNT(*) AS station_count
                FROM stations
                GROUP BY station_type
                ORDER BY
                    CASE station_type
                        WHEN '内涝水情站' THEN 1
                        WHEN '水库水位站' THEN 2
                        WHEN '河道水位站' THEN 3
                        ELSE 4
                    END,
                    station_type
                """
            ).fetchall()
            total = self._scalar(conn, "SELECT COUNT(*) FROM stations")

        return {
            "total": total,
            "district_stats_available": False,
            "district_stats_reason": "missing_coordinates",
            "items": [dict(row) for row in rows],
        }

    def get_data_status(self) -> dict[str, Any]:
        summary = self.get_database_summary()
        coordinate_status = self.get_station_coordinate_status()
        latest_observed_at = summary["flood_water_levels"]["observed_at_max"]
        return {
            "flood_water_levels": {
                "record_count": summary["flood_water_levels"]["rows"],
                "unique_station_codes": summary["flood_water_levels"][
                    "unique_station_codes"
                ],
                "observed_at_min": summary["flood_water_levels"]["observed_at_min"],
                "observed_at_max": latest_observed_at,
                "map_query_ready": True,
                "real_map_placement_ready": False,
            },
            "stations": {
                "total": coordinate_status["total_stations"],
                "coordinate_status": coordinate_status["status"],
                "has_coordinates": coordinate_status["has_coordinate_columns"],
                "missing_coordinate_stations": coordinate_status[
                    "missing_coordinate_stations"
                ],
            },
            "reservoir_water_levels": {
                "quality_role": "status_summary_only",
                "record_count": summary["reservoir_water_levels"]["rows"],
                "unique_station_codes": summary["reservoir_water_levels"][
                    "unique_station_codes"
                ],
                "null_water_level_rows": summary["reservoir_water_levels"][
                    "null_water_level_rows"
                ],
                "missing_station_codes": summary["reservoir_water_levels"][
                    "missing_station_codes"
                ],
            },
            "data_freshness": {
                "latest_observed_at": latest_observed_at,
                "status": "historical_snapshot",
                "message": (
                    "current local database is usable for API validation, "
                    "not live monitoring"
                ),
            },
        }

    def get_latest_import_batch(self) -> dict[str, Any]:
        with connect_readonly(self.settings) as conn:
            latest_imported_at = self._scalar(
                conn,
                "SELECT MAX(imported_at) FROM source_imports",
            )
            if latest_imported_at is None:
                return {
                    "latest_imported_at": None,
                    "import_count": 0,
                    "total_row_count": 0,
                    "items": [],
                }

            rows = conn.execute(
                """
                SELECT id, source_file, source_format, imported_at, row_count
                FROM source_imports
                WHERE imported_at = ?
                ORDER BY id
                """,
                (latest_imported_at,),
            ).fetchall()

        items = [dict(row) for row in rows]
        return {
            "latest_imported_at": latest_imported_at,
            "import_count": len(items),
            "total_row_count": sum(item["row_count"] for item in items),
            "items": items,
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

    def get_location_status(self) -> dict[str, Any]:
        coordinate_status = self.get_station_coordinate_status()
        with connect_readonly(self.settings) as conn:
            if not self._table_exists(conn, "location_candidates"):
                candidate_count = 0
                approved_count = 0
                rejected_count = 0
            else:
                candidate_count = self._scalar(
                    conn,
                    "SELECT COUNT(*) FROM location_candidates",
                )
                approved_count = self._scalar(
                    conn,
                    """
                    SELECT COUNT(*)
                    FROM location_candidates
                    WHERE review_status = 'approved'
                    """,
                )
                rejected_count = self._scalar(
                    conn,
                    """
                    SELECT COUNT(*)
                    FROM location_candidates
                    WHERE review_status = 'rejected'
                    """,
                )

        return {
            "total_stations": coordinate_status["total_stations"],
            "has_coordinate_columns": coordinate_status["has_coordinate_columns"],
            "coordinate_status": coordinate_status["status"],
            "candidate_count": candidate_count,
            "approved_count": approved_count,
            "rejected_count": rejected_count,
            "required_action": coordinate_status["required_action"],
        }

    def create_location_candidate(
        self,
        *,
        station_code: str,
        longitude: float,
        latitude: float,
        formatted_address: str,
        amap_level: str | None,
        amap_adcode: str | None,
        coord_source: str = "amap",
        coord_quality: str = "candidate",
        review_status: str = "pending",
    ) -> dict[str, Any]:
        now = self._utc_now()
        with connect_write(self.settings) as conn:
            cursor = conn.execute(
                """
                INSERT INTO location_candidates (
                    station_code,
                    longitude,
                    latitude,
                    formatted_address,
                    amap_level,
                    amap_adcode,
                    coord_source,
                    coord_quality,
                    review_status,
                    reviewed_at,
                    review_note,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?)
                """,
                (
                    station_code,
                    longitude,
                    latitude,
                    formatted_address,
                    amap_level,
                    amap_adcode,
                    coord_source,
                    coord_quality,
                    review_status,
                    now,
                    now,
                ),
            )
            candidate_id = cursor.lastrowid

        candidate = self.get_location_candidate(candidate_id)
        if candidate is None:
            raise RuntimeError("location candidate was not saved")
        return candidate

    def get_location_candidate(self, candidate_id: int) -> dict[str, Any] | None:
        with connect_readonly(self.settings) as conn:
            row = conn.execute(
                """
                SELECT
                    id,
                    station_code,
                    longitude,
                    latitude,
                    formatted_address,
                    amap_level,
                    amap_adcode,
                    coord_source,
                    coord_quality,
                    review_status,
                    reviewed_at,
                    review_note,
                    created_at,
                    updated_at
                FROM location_candidates
                WHERE id = ?
                """,
                (candidate_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def get_location_candidates(self, station_code: str) -> list[dict[str, Any]]:
        with connect_readonly(self.settings) as conn:
            if not self._table_exists(conn, "location_candidates"):
                return []
            rows = conn.execute(
                """
                SELECT
                    id,
                    station_code,
                    longitude,
                    latitude,
                    formatted_address,
                    amap_level,
                    amap_adcode,
                    coord_source,
                    coord_quality,
                    review_status,
                    reviewed_at,
                    review_note,
                    created_at,
                    updated_at
                FROM location_candidates
                WHERE station_code = ?
                ORDER BY created_at DESC, id DESC
                """,
                (station_code,),
            ).fetchall()
        return [dict(row) for row in rows]

    def review_location_candidate(
        self,
        *,
        station_code: str,
        candidate_id: int,
        review_status: str,
        review_note: str | None = None,
    ) -> dict[str, Any] | None:
        coord_quality = "verified" if review_status == "approved" else "rejected"
        now = self._utc_now()
        with connect_write(self.settings) as conn:
            cursor = conn.execute(
                """
                UPDATE location_candidates
                SET
                    review_status = ?,
                    coord_quality = ?,
                    reviewed_at = ?,
                    review_note = ?,
                    updated_at = ?
                WHERE id = ?
                    AND station_code = ?
                """,
                (
                    review_status,
                    coord_quality,
                    now,
                    review_note,
                    now,
                    candidate_id,
                    station_code,
                ),
            )
            if cursor.rowcount == 0:
                return None

        return self.get_location_candidate(candidate_id)
