import assert from 'node:assert/strict'
import { createRequire } from 'node:module'
import fs from 'node:fs'
import path from 'node:path'
import vm from 'node:vm'
import ts from 'typescript'

const require = createRequire(import.meta.url)
const root = process.cwd()
const sourcePath = path.join(root, 'src/utils/commandMap.ts')
const source = fs.readFileSync(sourcePath, 'utf8')
const { outputText } = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2020,
    esModuleInterop: true,
  },
})

const cjsModule = { exports: {} }
const sandbox = {
  exports: {},
  module: cjsModule,
  require,
}
sandbox.exports = cjsModule.exports
vm.runInNewContext(outputText, sandbox, { filename: sourcePath })
const logic = cjsModule.exports

const points = [
  {
    station_code: 'A',
    station_name: '南联桥洞',
    station_type: '内涝水情站',
    latest_observed_at: '2026-06-22T10:00:00',
    latest_water_level_m: 1.2,
    raw_water_level: '1.2',
    has_coordinates: true,
    coordinate_status: 'approved',
    longitude: 114.1,
    latitude: 22.6,
    coord_source: 'amap',
    coord_quality: 'verified',
    review_status: 'approved',
  },
  {
    station_code: 'B',
    station_name: '缺坐标点',
    station_type: '内涝水情站',
    latest_observed_at: '2026-06-22T10:05:00',
    latest_water_level_m: 0.2,
    raw_water_level: '0.2',
    has_coordinates: false,
    coordinate_status: 'missing_coordinates',
  },
]

const assessments = [
  {
    station_code: 'A',
    station_name: '南联桥洞',
    latest_observed_at: '2026-06-22T10:00:00',
    latest_water_level_m: 1.2,
    risk_level: 'warning',
    trend: 'rising',
    rule_version: 'flood_rule_v1',
    rule_description: '达到警戒阈值',
    generated_at: '2026-06-22T10:10:00',
  },
  {
    station_code: 'B',
    station_name: '缺坐标点',
    latest_observed_at: '2026-06-22T10:05:00',
    latest_water_level_m: 0.2,
    risk_level: 'normal',
    trend: 'stable',
    rule_version: 'flood_rule_v1',
    rule_description: '正常',
    generated_at: '2026-06-22T10:10:00',
  },
  {
    station_code: 'C',
    station_name: '关注点',
    latest_observed_at: '2026-06-22T10:06:00',
    latest_water_level_m: 0.8,
    risk_level: 'attention',
    trend: 'fluctuating',
    rule_version: 'flood_rule_v1',
    rule_description: '需关注',
    generated_at: '2026-06-22T10:10:00',
  },
]

assert.equal(JSON.stringify(logic.summarizeRisks(assessments).map((item) => [item.key, item.count])), JSON.stringify([
  ['danger', 0],
  ['warning', 1],
  ['attention', 1],
  ['normal', 1],
  ['no_data', 0],
]))

assert.equal(logic.getRenderablePoints(points).length, 1)
assert.equal(logic.getCoordinateCounts(points).withCoordinates, 1)
assert.equal(logic.getCoordinateCounts(points).missingCoordinates, 1)
assert.equal(logic.mergePointsWithAssessments(points, assessments)[0].risk_level, 'warning')
assert.equal(JSON.stringify(logic.getPriorityAssessments(assessments).map((item) => item.station_code)), JSON.stringify(['A', 'C']))

const normalOnly = assessments.map((item) => ({ ...item, risk_level: 'normal' }))
assert.equal(logic.getPriorityAssessments(normalOnly).length, 0)
assert.equal(logic.summarizeRisks(normalOnly).find((item) => item.key === 'normal').count, 3)
assert.equal(
  logic.formatObservationWindow('2026-01-01T00:00:00', '2026-06-23T00:47:39'),
  '2026-01-01 00:00 至 2026-06-23 00:47',
)
assert.equal(logic.formatObservationWindow(null, '2026-06-23T00:47:39'), '截至 2026-06-23 00:47')

assert.equal(
  JSON.stringify(logic.normalizeObservationWindow(
    {
      observed_at_min: '2025-12-31 23:50:23',
      observed_at_max: '2026-06-23 00:47:39',
      record_count: 4_101_063,
    },
    {
      observed_at_min: '2025-12-31 23:50:23',
      observed_at_max: '2026-06-23 00:47:39',
    },
    '2026-06-23 00:47:39',
  )),
  JSON.stringify({
    earliest: '2025-12-31 23:50:23',
    latest: '2026-06-23 00:47:39',
    recordCount: 4_101_063,
  }),
)

assert.equal(
  JSON.stringify(logic.getStatusCoordinateCounts(
    {
      missing_coordinate_stations: 485,
    },
    {
      candidate_count: 8,
      approved_count: 5,
    },
  )),
  JSON.stringify({
    missing: 485,
    candidates: 8,
    approved: 5,
  }),
)

assert.equal(logic.getAssessmentTargetIndex(assessments, 'B'), 1)
assert.equal(logic.getAssessmentTargetIndex(assessments, 'missing'), -1)
assert.equal(logic.shouldHighlightAssessment('B', 'B'), true)
assert.equal(logic.shouldHighlightAssessment('A', 'B'), false)
assert.equal(logic.formatWaterLevelAxisLabel(0.024), '0.024')
assert.equal(logic.formatWaterLevelAxisLabel(1.2), '1.200')
assert.equal(
  JSON.stringify(logic.summarizeWaterLevelRecords([
    { observed_at: '2026-06-22T10:00:00', water_level_m: 0, raw_water_level: '0' },
    { observed_at: '2026-06-22T10:01:00', water_level_m: 0.024, raw_water_level: '0.024' },
    { observed_at: '2026-06-22T10:02:00', water_level_m: null, raw_water_level: '' },
    { observed_at: '2026-06-22T10:03:00', water_level_m: 0.12, raw_water_level: '0.12' },
  ])),
  JSON.stringify({
    count: 3,
    nullCount: 1,
    min: 0,
    max: 0.12,
    avg: 0.048,
  }),
)

console.log('command map logic tests passed')
