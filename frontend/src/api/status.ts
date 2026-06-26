import client from './client'
import type { DataStatusResponse, TimeRangeResponse, LatestImportResponse } from '../types/api'

export async function getDataStatus(): Promise<DataStatusResponse> {
  const res = await client.get<DataStatusResponse>('/api/status/data')
  return res.data
}

export async function getTimeRange(): Promise<TimeRangeResponse> {
  const res = await client.get<TimeRangeResponse>('/api/data/time-range')
  return res.data
}

export async function getLatestImport(): Promise<LatestImportResponse> {
  const res = await client.get<LatestImportResponse>('/api/imports/latest')
  return res.data
}
