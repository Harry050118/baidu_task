# Day 6 Statistics And Status API Design

> Date: 2026-06-25  
> Scope: Day 6 backend statistics and data status APIs

## Context

Day 5 added the first FastAPI monitoring endpoints:

- `GET /health`
- `GET /api/map/points`
- `GET /api/points/{station_code}`
- `GET /api/points/{station_code}/history`
- `GET /api/data/time-range`

The Day 6 goal is to add read-only statistics and data status APIs for the future frontend data status page and map statistics panel.

The SQLite mainline database remains `data/local/shenzhen_water.db`. The mainline business tables are `stations` and `flood_water_levels`. `reservoir_water_levels` is only a side-channel quality summary and must not enter map points, station risk logic, or mainline flood statistics.

## API Scope

Day 6 will implement three endpoints:

- `GET /api/stats/overview`
- `GET /api/status/data`
- `GET /api/imports/latest`

Day 6 will not implement `GET /api/stats/stations` unless the frontend needs station-type distribution immediately. The current minimum scope keeps the backend focused on confirmed Day 6 needs.

## Endpoint Design

### `GET /api/stats/overview`

Purpose: provide the top-level map statistics panel facts without doing risk assessment.

Data source:

- `stations`
- `flood_water_levels`

Response fields:

| Field | Value |
|---|---:|
| `flood_station_count` | `148` |
| `latest_observed_at` | `2026-06-23 00:47:39` |
| `flood_record_count` | `4,101,063` |
| `stations_total` | `485` |
| `coordinate_status` | `missing_coordinates` |
| `has_coordinates` | `false` |

This endpoint will not return risk-level counts. Risk assessment belongs to a later day.

### `GET /api/status/data`

Purpose: provide the future data status page with data range, coordinate readiness, and quality summary.

Response sections:

- `flood_water_levels`
- `stations`
- `reservoir_water_levels`

`flood_water_levels` will include:

- `record_count`
- `unique_station_codes`
- `observed_at_min`
- `observed_at_max`
- `map_query_ready=true`
- `real_map_placement_ready=false`

`stations` will include:

- `total`
- `coordinate_status=missing_coordinates`
- `has_coordinates=false`
- `missing_coordinate_stations=485`

`reservoir_water_levels` will include only side-channel quality fields:

- `quality_role=status_summary_only`
- `record_count`
- `unique_station_codes`
- `null_water_level_rows`
- `missing_station_codes`

This endpoint must make clear that data can support flood station queries, but cannot support accurate real map placement because station coordinates are missing.

### `GET /api/imports/latest`

Purpose: expose the latest import batch summary from real `source_imports` records.

Confirmed table schema:

| Column | Type |
|---|---|
| `id` | `INTEGER PRIMARY KEY AUTOINCREMENT` |
| `source_file` | `TEXT NOT NULL` |
| `source_format` | `TEXT NOT NULL` |
| `imported_at` | `TEXT NOT NULL` |
| `row_count` | `INTEGER NOT NULL` |

The current database has 13 import rows, all with `imported_at=2026-06-23T06:43:59+00:00`. Because the table has no status or error columns, the API must not invent success, failure, or error details.

Response fields:

- `latest_imported_at`
- `import_count`
- `total_row_count`
- `items`

`items` will contain the real `id`, `source_file`, `source_format`, `imported_at`, and `row_count` fields for rows in the latest import timestamp, ordered by `id`.

## Implementation Boundaries

Day 6 will:

- Keep API code in `backend/app/api/routes.py`.
- Add repository methods to `backend/app/repositories/water_repository.py`.
- Keep database access read-only through the existing `connect_readonly` helper.
- Reuse the existing coordinate status logic where possible.
- Add a focused `tests/test_backend_day6.py`.

Day 6 will not:

- Modify `.env`.
- Print or expose `APP_KEY` or `AMAP_WEB_SERVICE_KEY`.
- Re-run full data downloads or import archives.
- Batch-fill coordinates.
- Invent coordinates.
- Add risk assessment or model prediction.
- Treat reservoir water levels as flood risk mainline data.
- Preserve unrelated `docs/data_quality_report.md` refresh diffs if any script accidentally updates it.
- Add the untracked Day 4 document to Day 6 work.

## Testing

Tests will cover:

- The FastAPI app still starts and `/health` remains available.
- `/api/stats/overview` returns the confirmed Day 3 and Day 5 facts.
- `/api/status/data` reports missing coordinates and `real_map_placement_ready=false`.
- `reservoir_water_levels` appears only as `status_summary_only` quality data.
- `/api/imports/latest` returns real records from `source_imports`, with 13 latest import rows and the real total row count.
- Full `unittest` discovery still passes.

## Acceptance Criteria

Day 6 is complete when:

- The three endpoints return stable JSON matching the design above.
- The implementation uses only read-only SQLite queries.
- Tests pass for Day 6 and the full existing suite.
- The repository worktree does not include unrelated Day 4 or data quality report changes.
