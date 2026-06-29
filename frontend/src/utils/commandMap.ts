import type { AssessmentItem, MapPoint, RiskLevel, WaterLevelRecord } from '../types/api'

export type MapPointWithRisk = MapPoint & { risk_level: RiskLevel }

export interface RiskSummaryItem {
  key: RiskLevel
  label: string
  color: string
  count: number
}

export interface CoordinateCounts {
  total: number
  withCoordinates: number
  missingCoordinates: number
}

export interface NormalizedObservationWindow {
  earliest: string | null
  latest: string | null
  recordCount: number | null
}

export interface StatusCoordinateCounts {
  missing: number | null
  candidates: number | null
  approved: number | null
}

export interface WaterLevelSummary {
  count: number
  nullCount: number
  min: number | null
  max: number | null
  avg: number | null
}

const RISK_ORDER: RiskLevel[] = ['danger', 'warning', 'attention', 'normal', 'no_data']

const RISK_META: Record<RiskLevel, { label: string; color: string; priority: number }> = {
  danger: { label: '危险', color: '#DA3633', priority: 0 },
  warning: { label: '警戒', color: '#D29922', priority: 1 },
  attention: { label: '关注', color: '#9E6A03', priority: 2 },
  normal: { label: '正常', color: '#238636', priority: 3 },
  no_data: { label: '无数据', color: '#484F58', priority: 4 },
}

export function getRenderablePoints(points: MapPoint[]): MapPoint[] {
  return points.filter(
    (point) =>
      point.has_coordinates &&
      point.coordinate_status === 'approved' &&
      typeof point.longitude === 'number' &&
      typeof point.latitude === 'number',
  )
}

export function getCoordinateCounts(points: MapPoint[]): CoordinateCounts {
  const withCoordinates = getRenderablePoints(points).length
  return {
    total: points.length,
    withCoordinates,
    missingCoordinates: Math.max(points.length - withCoordinates, 0),
  }
}

export function mergePointsWithAssessments(
  points: MapPoint[],
  assessments: AssessmentItem[],
): MapPointWithRisk[] {
  const assessmentByCode = new Map(assessments.map((item) => [item.station_code, item]))
  return points.map((point) => ({
    ...point,
    risk_level: assessmentByCode.get(point.station_code)?.risk_level ?? 'no_data',
  }))
}

export function summarizeRisks(assessments: AssessmentItem[]): RiskSummaryItem[] {
  const counts = new Map<RiskLevel, number>()
  for (const item of assessments) {
    counts.set(item.risk_level, (counts.get(item.risk_level) ?? 0) + 1)
  }
  return RISK_ORDER.map((key) => ({
    key,
    label: RISK_META[key].label,
    color: RISK_META[key].color,
    count: counts.get(key) ?? 0,
  }))
}

export function getPriorityAssessments(assessments: AssessmentItem[]): AssessmentItem[] {
  return assessments
    .filter((item) => ['danger', 'warning', 'attention'].includes(item.risk_level))
    .sort((a, b) => {
      const riskDelta = RISK_META[a.risk_level].priority - RISK_META[b.risk_level].priority
      if (riskDelta !== 0) return riskDelta
      return (b.latest_water_level_m ?? -Infinity) - (a.latest_water_level_m ?? -Infinity)
    })
}

export function formatObservationWindow(start: string | null, end: string | null): string {
  if (start && end) return `${formatDateTime(start)} 至 ${formatDateTime(end)}`
  if (end) return `截至 ${formatDateTime(end)}`
  if (start) return `起始 ${formatDateTime(start)}`
  return '—'
}

export function normalizeObservationWindow(
  statusFlood: Record<string, unknown> | null | undefined,
  timeRangeFlood: Record<string, unknown> | null | undefined,
  fallbackLatest: string | null = null,
): NormalizedObservationWindow {
  const earliest =
    stringOrNull(statusFlood?.earliest_observed_at) ??
    stringOrNull(statusFlood?.observed_at_min) ??
    stringOrNull(timeRangeFlood?.earliest_observed_at) ??
    stringOrNull(timeRangeFlood?.observed_at_min)
  const latest =
    stringOrNull(statusFlood?.latest_observed_at) ??
    stringOrNull(statusFlood?.observed_at_max) ??
    stringOrNull(timeRangeFlood?.latest_observed_at) ??
    stringOrNull(timeRangeFlood?.observed_at_max) ??
    fallbackLatest
  const recordCount =
    numberOrNull(statusFlood?.record_count) ??
    numberOrNull(timeRangeFlood?.record_count)

  return { earliest, latest, recordCount }
}

export function getStatusCoordinateCounts(
  statusStations: Record<string, unknown> | null | undefined,
  locationStatus: Record<string, unknown> | null | undefined,
): StatusCoordinateCounts {
  return {
    missing:
      numberOrNull(statusStations?.missing_coordinates) ??
      numberOrNull(statusStations?.missing_coordinate_stations),
    candidates:
      numberOrNull(statusStations?.candidate_count) ??
      numberOrNull(locationStatus?.candidate_count),
    approved:
      numberOrNull(statusStations?.approved_count) ??
      numberOrNull(locationStatus?.approved_count),
  }
}

export function getAssessmentTargetIndex(items: AssessmentItem[], targetStationCode: string | null): number {
  if (!targetStationCode) return -1
  return items.findIndex((item) => item.station_code === targetStationCode)
}

export function shouldHighlightAssessment(stationCode: string, targetStationCode: string | null): boolean {
  return Boolean(targetStationCode && stationCode === targetStationCode)
}

export function formatWaterLevelAxisLabel(value: number): string {
  return value.toFixed(3)
}

export function summarizeWaterLevelRecords(records: WaterLevelRecord[]): WaterLevelSummary {
  const values = records
    .map((record) => record.water_level_m)
    .filter((value): value is number => typeof value === 'number' && Number.isFinite(value))
  const nullCount = records.length - values.length

  if (values.length === 0) {
    return {
      count: 0,
      nullCount,
      min: null,
      max: null,
      avg: null,
    }
  }

  const min = Math.min(...values)
  const max = Math.max(...values)
  const avg = values.reduce((sum, value) => sum + value, 0) / values.length
  return {
    count: values.length,
    nullCount,
    min: roundWaterLevel(min),
    max: roundWaterLevel(max),
    avg: roundWaterLevel(avg),
  }
}

function formatDateTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  const hour = `${date.getHours()}`.padStart(2, '0')
  const minute = `${date.getMinutes()}`.padStart(2, '0')
  return `${year}-${month}-${day} ${hour}:${minute}`
}

function stringOrNull(value: unknown): string | null {
  return typeof value === 'string' && value.length > 0 ? value : null
}

function numberOrNull(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

function roundWaterLevel(value: number): number {
  return Number(value.toFixed(6))
}
