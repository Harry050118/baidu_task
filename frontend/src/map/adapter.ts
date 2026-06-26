// MapAdapter interface — no keys or SDK calls here
import type { MapPoint } from '../types/api'

export interface MapAdapter {
  /** Mount the map/workspace into the given container element */
  mount(container: HTMLElement): void
  /** Render points on the workspace */
  renderPoints(points: MapPoint[]): void
  /** Register a click handler for a station */
  onPointClick(handler: (stationCode: string) => void): void
  /** Destroy and clean up */
  destroy(): void
}

// NOTE: Real map adapters (e.g. Amap JS API) must be integrated separately
// with a secure key injection mechanism. This file must NEVER contain any API key.
