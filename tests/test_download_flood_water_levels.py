from __future__ import annotations

import argparse
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts import download_flood_water_levels as downloader


class DownloadFloodWaterLevelsTest(unittest.TestCase):
    def test_month_date_range_uses_real_calendar_month_end(self) -> None:
        self.assertEqual(downloader.month_date_range("202601"), ("20260101", "20260131"))
        self.assertEqual(downloader.month_date_range("202602"), ("20260201", "20260228"))
        self.assertEqual(downloader.month_date_range("202402"), ("20240201", "20240229"))

    def test_month_output_paths_keep_each_month_in_own_directory(self) -> None:
        dataset = downloader.DATASETS["flood"]
        output_dir, csv_path = downloader.month_output_paths(
            Path("/tmp/out"), "202601", dataset
        )

        self.assertEqual(output_dir, Path("/tmp/out/2026-01"))
        self.assertEqual(
            csv_path,
            Path("/tmp/out/2026-01/市水务局积涝点水位数据_2920001403147_202601.csv"),
        )

    def test_reservoir_dataset_uses_reservoir_api_and_output_paths(self) -> None:
        dataset = downloader.DATASETS["reservoir"]
        output_dir, csv_path = downloader.month_output_paths(
            Path("/tmp/out"), "202601", dataset
        )

        self.assertEqual(
            dataset.url,
            "https://opendata.sz.gov.cn/api/1952552493/1/service.xhtml",
        )
        self.assertEqual(dataset.csv_fields, ["测站编码", "自增ID", "时水位（m）", "采集时间"])
        self.assertEqual(output_dir, Path("/tmp/out/2026-01"))
        self.assertEqual(
            csv_path,
            Path("/tmp/out/2026-01/市水务局水库水位表_1952552493_202601.csv"),
        )

    def test_reservoir_rows_are_normalized_to_csv_fields(self) -> None:
        dataset = downloader.DATASETS["reservoir"]

        self.assertEqual(
            downloader.normalize_row(
                {"STCD": "ST001", "ID": "42", "RZ": "12.3", "TM": "2026-01-01 00:00:00"},
                dataset,
            ),
            {
                "测站编码": "ST001",
                "自增ID": "42",
                "时水位（m）": "12.3",
                "采集时间": "2026-01-01 00:00:00",
            },
        )

    def test_station_dataset_uses_station_api_and_output_paths(self) -> None:
        dataset = downloader.DATASETS["station"]

        self.assertEqual(
            dataset.url,
            "https://opendata.sz.gov.cn/api/1392394662/1/service.xhtml",
        )
        self.assertEqual(dataset.csv_fields, ["测站编码", "测站名称", "站类"])
        self.assertEqual(
            downloader.normalize_row(
                {
                    "STCD": "MS1104403070000342",
                    "STNM": "(市)布吉站（深圳东站）",
                    "STTP": "内涝水情站",
                },
                dataset,
            ),
            {
                "测站编码": "MS1104403070000342",
                "测站名称": "(市)布吉站（深圳东站）",
                "站类": "内涝水情站",
            },
        )

    def test_station_request_params_do_not_include_date_range(self) -> None:
        dataset = downloader.DATASETS["station"]

        self.assertEqual(
            downloader.build_request_params(
                page=1,
                rows=10000,
                start_date="20260601",
                end_date="20260623",
                app_key="abc123",
                dataset=dataset,
            ),
            {"page": 1, "rows": 10000, "appKey": "abc123"},
        )

    def test_station_dataset_rejects_month_downloads(self) -> None:
        args = argparse.Namespace(dataset="station", months=["202601"])

        with self.assertRaisesRegex(ValueError, "does not support --months"):
            downloader.validate_args(args)

    def test_load_app_key_strips_chinese_quotes_from_env_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            env_file.write_text("APP_KEY=“abc123”\n", encoding="utf-8")
            args = argparse.Namespace(app_key=None, env_file=env_file)

            self.assertEqual(downloader.load_app_key(args), "abc123")


if __name__ == "__main__":
    unittest.main()
