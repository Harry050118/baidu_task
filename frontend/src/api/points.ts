import client from './client'
import type { PointDetailResponse, PointHistoryResponse, AssessmentItem } from '../types/api'

export async function getPoint(stationCode: string): Promise<PointDetailResponse> {
  const res = await client.get<PointDetailResponse>(`/api/points/${stationCode}`)
  return res.data
}

export async function getHistory(stationCode: string, limit = 500): Promise<PointHistoryResponse> {
  const res = await client.get<PointHistoryResponse>(`/api/points/${stationCode}/history`, {
    params: { limit },
  })
  return res.data
}

export async function getPointAssessment(stationCode: string): Promise<AssessmentItem> {
  const res = await client.get<AssessmentItem>(`/api/points/${stationCode}/assessment`)
  return res.data
}
