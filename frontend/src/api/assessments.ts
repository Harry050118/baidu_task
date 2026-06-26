import client from './client'
import type { AssessmentsResponse } from '../types/api'

export async function getAssessments(): Promise<AssessmentsResponse> {
  const res = await client.get<AssessmentsResponse>('/api/assessments')
  return res.data
}
