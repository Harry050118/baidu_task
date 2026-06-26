import client from './client'
import type { OverviewResponse, StationsStatsResponse } from '../types/api'

export async function getOverview(): Promise<OverviewResponse> {
  const res = await client.get<OverviewResponse>('/api/stats/overview')
  return res.data
}

export async function getStations(): Promise<StationsStatsResponse> {
  const res = await client.get<StationsStatsResponse>('/api/stats/stations')
  return res.data
}
