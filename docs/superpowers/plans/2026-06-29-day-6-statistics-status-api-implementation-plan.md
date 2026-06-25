# Day 6 统计与状态 API 实施计划

> **给执行代理的要求：** 实施本计划时，按任务清单逐项执行；改代码前先写失败测试，再写最小实现，最后跑全量测试。

**目标：** 实现深圳积水监测后端 Day 6 只读统计、数据状态和最近导入批次 API。

**架构：** 延续 Day 5 结构，不拆新路由模块。只在 `backend/app/repositories/water_repository.py` 增加只读查询方法，在 `backend/app/api/routes.py` 暴露 3 个接口，并通过 `tests/test_backend_day6.py` 固定接口行为。

**技术栈：** Python、FastAPI、SQLite 只读连接、`unittest`、FastAPI `TestClient`。

---

### 任务 1：新增 Day 6 失败测试

**文件：**

- 新增：`tests/test_backend_day6.py`

- [ ] **步骤 1：写 3 个 Day 6 接口测试**

```python
from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from backend.app.main import app


class BackendDay6StatsApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_stats_overview_reports_mainline_flood_facts(self) -> None:
        response = self.client.get("/api/stats/overview")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["flood_station_count"], 148)
        self.assertEqual(payload["latest_observed_at"], "2026-06-23 00:47:39")
        self.assertEqual(payload["flood_record_count"], 4_101_063)
        self.assertEqual(payload["stations_total"], 485)
        self.assertEqual(payload["coordinate_status"], "missing_coordinates")
        self.assertFalse(payload["has_coordinates"])
        self.assertNotIn("risk_levels", payload)
        self.assertNotIn("reservoir_water_levels", payload)


class BackendDay6DataStatusApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_status_data_reports_coordinate_gap_and_reservoir_quality_side_channel(self) -> None:
        response = self.client.get("/api/status/data")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["flood_water_levels"]["record_count"], 4_101_063)
        self.assertEqual(payload["flood_water_levels"]["unique_station_codes"], 148)
        self.assertTrue(payload["flood_water_levels"]["map_query_ready"])
        self.assertFalse(payload["flood_water_levels"]["real_map_placement_ready"])
        self.assertEqual(payload["stations"]["total"], 485)
        self.assertEqual(payload["stations"]["coordinate_status"], "missing_coordinates")
        self.assertFalse(payload["stations"]["has_coordinates"])
        self.assertEqual(payload["stations"]["missing_coordinate_stations"], 485)
        self.assertEqual(
            payload["reservoir_water_levels"]["quality_role"],
            "status_summary_only",
        )
        self.assertEqual(payload["reservoir_water_levels"]["record_count"], 2_040_352)
        self.assertEqual(payload["reservoir_water_levels"]["null_water_level_rows"], 40_982)
        self.assertEqual(payload["data_freshness"]["status"], "historical_snapshot")
        self.assertEqual(
            payload["data_freshness"]["latest_observed_at"],
            "2026-06-23 00:47:39",
        )


class BackendDay6ImportsApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_imports_latest_returns_real_source_import_rows(self) -> None:
        response = self.client.get("/api/imports/latest")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["latest_imported_at"], "2026-06-23T06:43:59+00:00")
        self.assertEqual(payload["import_count"], 13)
        self.assertEqual(payload["total_row_count"], 6_141_915)
        self.assertEqual(len(payload["items"]), 13)
        self.assertEqual(payload["items"][0]["id"], 7)
        self.assertEqual(payload["items"][-1]["id"], 19)
        for item in payload["items"]:
            self.assertEqual(item["source_format"], "csv")
            self.assertIn("source_file", item)
            self.assertIn("row_count", item)
            self.assertNotIn("status", item)
            self.assertNotIn("error", item)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **步骤 2：运行 Day 6 测试并确认 RED**

运行：

```bash
.venv/bin/python -m unittest tests/test_backend_day6.py
```

预期：接口尚未实现，测试因 `404 Not Found` 失败。

### 任务 2：实现 Repository 只读查询

**文件：**

- 修改：`backend/app/repositories/water_repository.py`

- [ ] **步骤 1：新增只读查询方法**

新增方法：

- `get_stats_overview()`
- `get_data_status()`
- `get_latest_import_batch()`

实现口径：

- `get_stats_overview()` 只汇总 `stations` 和 `flood_water_levels`。
- `get_data_status()` 返回积涝主线、坐标状态、水库旁路质量摘要和 `data_freshness`。
- `get_latest_import_batch()` 用 `MAX(imported_at)` 找最近导入时间，再按 `id` 升序返回该时间下的真实记录。

- [ ] **步骤 2：保持数据库只读**

所有新增方法必须使用现有 `connect_readonly(self.settings)` 或既有只读汇总方法，不写入数据库。

### 任务 3：新增 API 路由

**文件：**

- 修改：`backend/app/api/routes.py`

- [ ] **步骤 1：新增 3 个路由**

新增：

- `GET /stats/overview`
- `GET /status/data`
- `GET /imports/latest`

每个路由直接返回对应 repository 方法结果。

### 任务 4：验证与提交

**文件：**

- 新增：`tests/test_backend_day6.py`
- 修改：`backend/app/api/routes.py`
- 修改：`backend/app/repositories/water_repository.py`
- 新增：`docs/superpowers/plans/2026-06-29-day-6-statistics-status-api-implementation-plan.md`

- [ ] **步骤 1：运行 Day 6 测试**

运行：

```bash
.venv/bin/python -m unittest tests/test_backend_day6.py
```

预期：`OK`。

- [ ] **步骤 2：运行全量测试**

运行：

```bash
.venv/bin/python -m unittest discover tests
```

预期：全部通过。

- [ ] **步骤 3：检查工作树**

运行：

```bash
git status --short
```

预期：没有无关 `docs/data_quality_report.md` 变化，也不暂存未跟踪 Day 4 文档。
