import client from './client'
import type {
  LocationsStatusResponse,
  LocationCandidatesResponse,
  GeocodeRequest,
  ReviewRequest,
} from '../types/api'

export async function getLocationsStatus(): Promise<LocationsStatusResponse> {
  const res = await client.get<LocationsStatusResponse>('/api/locations/status')
  return res.data
}

export async function getCandidates(stationCode: string): Promise<LocationCandidatesResponse> {
  const res = await client.get<LocationCandidatesResponse>(`/api/locations/${stationCode}/candidates`)
  return res.data
}

export async function geocode(payload: GeocodeRequest): Promise<LocationCandidatesResponse> {
  const res = await client.post<LocationCandidatesResponse>('/api/locations/geocode-candidates', payload)
  return res.data
}

export async function review(stationCode: string, payload: ReviewRequest): Promise<unknown> {
  const res = await client.post(`/api/locations/${stationCode}/review`, payload)
  return res.data
}
