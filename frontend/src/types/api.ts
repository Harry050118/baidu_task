// TS types strictly matching Day 9 API contract

export type RiskLevel = 'danger' | 'warning' | 'attention' | 'normal' | 'no_data'
export type Trend = 'rising' | 'falling' | 'stable' | 'fluctuating' | 'no_data'
export type CoordinateStatus = 'missing_coordinates' | 'approved' | 'pending' | 'rejected'
export type ReviewStatus = 'approved' | 'rejected' | 'pending'

// GET /health
export interface HealthResponse {
  status: 'ok'
  database: {
    status: 'ok'
    path: string
    tables: string[]
  }
}

// GET /api/map/points
export interface MapPoint {
  station_code: string
  station_name: string
  station_type: string
  latest_observed_at: string | null
  latest_water_level_m: number | null
  raw_water_level: string | null
  has_coordinates: boolean
  coordinate_status: CoordinateStatus
  // only when has_coordinates=true
  longitude?: number
  latitude?: number
  coord_source?: string
  coord_quality?: string
  review_status?: ReviewStatus
}

export interface MapPointsResponse {
  points: MapPoint[]
}

// GET /api/points/{station_code}
export interface PointDetailResponse {
  station: {
    station_code: string
    station_name: string
    station_type: string
  }
  latest_water_level: {
    water_level_m: number | null
    observed_at: string | null
    raw_water_level: string | null
  } | null
  coordinates: {
    coordinate_status: CoordinateStatus
    longitude?: number
    latitude?: number
    coord_source?: string
    review_status?: ReviewStatus
  }
}

// GET /api/points/{station_code}/history
export interface WaterLevelRecord {
  id: number
  observed_at: string
  water_level_m: number | null
  raw_water_level: string | null
}

export interface PointHistoryResponse {
  station: {
    station_code: string
    station_name: string
  }
  items: WaterLevelRecord[]
}

// GET /api/data/time-range
export interface TimeRangeResponse {
  flood_water_levels: {
    earliest_observed_at: string | null
    latest_observed_at: string | null
    record_count: number
  }
  reservoir_water_levels: {
    quality_role: 'status_summary_only'
    [key: string]: unknown
  }
}

// GET /api/stats/overview
export interface OverviewResponse {
  flood_station_count: number
  latest_observed_at: string | null
  flood_record_count: number
  stations_total: number
  coordinate_status: string
  has_coordinates: boolean
}

// GET /api/stats/stations
export interface StationsStatsResponse {
  total: number
  district_stats_available: false
  district_stats_reason: string
  items: Array<{ station_type: string; count: number }>
}

// GET /api/status/data
export interface DataStatusResponse {
  flood_water_levels: {
    earliest_observed_at: string | null
    latest_observed_at: string | null
    record_count: number
    is_available: boolean
  }
  stations: {
    total: number
    missing_coordinates: number
    candidate_count: number
    approved_count: number
  }
  reservoir_water_levels: {
    quality_role: 'status_summary_only'
    [key: string]: unknown
  }
  data_freshness: {
    status: string
    label: string
  }
}

// GET /api/imports/latest
export interface ImportBatchItem {
  imported_at: string
  record_count: number
  [key: string]: unknown
}

export interface LatestImportResponse {
  latest_imported_at: string | null
  import_count: number
  total_row_count: number
  items: ImportBatchItem[]
}

// GET /api/locations/status
export interface LocationsStatusResponse {
  total_stations: number
  has_coordinate_columns: boolean
  coordinate_status: CoordinateStatus
  candidate_count: number
  approved_count: number
  rejected_count: number
  required_action: string
}

// GET /api/locations/{station_code}/candidates
export interface LocationCandidate {
  id: number
  station_code: string
  longitude: number
  latitude: number
  coord_source: string
  review_status: ReviewStatus
  review_note: string | null
  created_at: string
}

export interface LocationCandidatesResponse {
  station: {
    station_code: string
    station_name: string
  }
  items: LocationCandidate[]
}

// POST /api/locations/geocode-candidates
export interface GeocodeRequest {
  station_code: string
  address?: string
}

// POST /api/locations/{station_code}/review
export interface ReviewRequest {
  candidate_id: number
  review_status: 'approved' | 'rejected'
  review_note?: string
}

// GET /api/assessments
export interface AssessmentItem {
  station_code: string
  station_name: string
  latest_observed_at: string | null
  latest_water_level_m: number | null
  risk_level: RiskLevel
  trend: Trend
  rule_version: string
  rule_description: string
  generated_at: string
}

export interface AssessmentsResponse {
  items: AssessmentItem[]
}
