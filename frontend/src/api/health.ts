import client from './client'
import type { HealthResponse } from '../types/api'

export async function getHealth(): Promise<HealthResponse> {
  const res = await client.get<HealthResponse>('/health')
  return res.data
}
