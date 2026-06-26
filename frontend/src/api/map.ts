import client from './client'
import type { MapPointsResponse } from '../types/api'

export async function getMapPoints(): Promise<MapPointsResponse> {
  const res = await client.get<MapPointsResponse>('/api/map/points')
  return res.data
}
