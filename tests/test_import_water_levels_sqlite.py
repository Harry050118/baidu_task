from __future__ import annotations

import csv
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts import import_water_levels_sqlite as importer


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class ImportWaterLevelsSqliteTest(unittest.TestCase):
    def test_discovers_monthly_csvs_in_sorted_order(self) -> None:
        with TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            write_csv(
                base / "2026-02" / "市水务局水库水位表_1952552493_202602.csv",
                importer.WATER_LEVEL_FIELDS,
                [],
            )
            write_csv(
                base / "2026-01" / "市水务局水库水位表_1952552493_202601.csv",
                importer.WATER_LEVEL_FIELDS,
                [],
            )

            self.assertEqual(
                [path.name for path in importer.discover_csv_files(base, "市水务局水库水位表_1952552493_*.csv")],
                [
                    "市水务局水库水位表_1952552493_202601.csv",
                    "市水务局水库水位表_1952552493_202602.csv",
                ],
            )

    def test_imports_current_download_structure_into_sqlite(self) -> None:
        with TemporaryDirectory(dir=importer.PROJECT_ROOT) as temp_dir:
            root = Path(temp_dir)
            stations_csv = root / "download" / "市水务局测站基本信息表" / "市水务局测站基本信息表_1392394662.csv"
            reservoir_dir = root / "download" / "市水务局水库水位表"
            flood_dir = root / "download" / "市水务局积涝水位数据"
            db_path = root / "data" / "local" / "test.db"

            write_csv(
                stations_csv,
                importer.STATION_FIELDS,
                [{"测站编码": "ST001", "测站名称": "测试站", "站类": "内涝水情站"}],
            )
            write_csv(
                reservoir_dir / "2026-01" / "市水务局水库水位表_1952552493_202601.csv",
                importer.WATER_LEVEL_FIELDS,
                [
                    {
                        "测站编码": "ST001",
                        "自增ID": "R1",
                        "时水位（m）": "1.23",
                        "采集时间": "2026-01-01 00:00:00",
                    }
                ],
            )
            write_csv(
                flood_dir / "2026-01" / "市水务局积涝点水位数据_2920001403147_202601.csv",
                importer.FLOOD_WATER_LEVEL_FIELDS,
                [
                    {
                        "测站编码": "ST001",
                        "时间": "2026-01-01 00:01:00",
                        "水位（m）": "0.02",
                        "水位id": "F1",
                    }
                ],
            )

            station_count, flood_count, reservoir_count = importer.import_csv(
                reservoir_csv_paths=importer.discover_csv_files(
                    reservoir_dir, importer.RESERVOIR_CSV_PATTERN
                ),
                stations_csv_path=stations_csv,
                flood_csv_paths=importer.discover_csv_files(
                    flood_dir, importer.FLOOD_CSV_PATTERN
                ),
                db_path=db_path,
                replace=True,
            )

            self.assertEqual((station_count, flood_count, reservoir_count), (1, 1, 1))
            with sqlite3.connect(db_path) as conn:
                self.assertEqual(
                    conn.execute("SELECT COUNT(*) FROM stations").fetchone()[0], 1
                )
                self.assertEqual(
                    conn.execute("SELECT COUNT(*) FROM flood_water_levels").fetchone()[0],
                    1,
                )
                self.assertEqual(
                    conn.execute("SELECT COUNT(*) FROM reservoir_water_levels").fetchone()[0],
                    1,
                )

    def test_blank_reservoir_water_level_imports_as_null(self) -> None:
        self.assertIsNone(importer.parse_water_level(""))
        self.assertIsNone(importer.parse_water_level(" "))
        self.assertIsNone(importer.parse_water_level("-"))


if __name__ == "__main__":
    unittest.main()
