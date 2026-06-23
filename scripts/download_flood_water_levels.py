#!/usr/bin/env python3
"""
Download flooding-point water-level data from the Shenzhen open-data API.

The API is paginated. This script saves each raw JSON page and writes one
combined CSV whose header matches scripts/import_water_levels_sqlite.py.
"""

from __future__ import annotations

import argparse
import calendar
import csv
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_URL = "https://opendata.sz.gov.cn/api/2920001403147/1/service.xhtml"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "download" / "市水务局积涝水位数据"
DEFAULT_CSV = DEFAULT_OUTPUT_DIR / "市水务局积涝点水位数据_2920001403147.csv"
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"
CSV_FIELDS = ["测站编码", "时间", "水位（m）", "水位id"]


@dataclass(frozen=True)
class DatasetConfig:
    key: str
    name: str
    url: str
    output_dir: Path
    csv_basename: str
    csv_fields: list[str]
    row_mapper: Callable[[dict[str, Any]], dict[str, Any]]
    include_date_params: bool = True


def normalize_flood_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "测站编码": row.get("CZBM", ""),
        "时间": row.get("SJ", ""),
        "水位（m）": row.get("SW", ""),
        "水位id": row.get("ID", ""),
    }


def normalize_reservoir_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "测站编码": row.get("STCD", ""),
        "自增ID": row.get("ID", ""),
        "时水位（m）": row.get("RZ", ""),
        "采集时间": row.get("TM", ""),
    }


def normalize_station_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "测站编码": row.get("STCD", ""),
        "测站名称": row.get("STNM", ""),
        "站类": row.get("STTP", ""),
    }


DATASETS = {
    "flood": DatasetConfig(
        key="flood",
        name="市水务局积涝点水位数据",
        url="https://opendata.sz.gov.cn/api/2920001403147/1/service.xhtml",
        output_dir=DEFAULT_OUTPUT_DIR,
        csv_basename="市水务局积涝点水位数据_2920001403147",
        csv_fields=CSV_FIELDS,
        row_mapper=normalize_flood_row,
    ),
    "reservoir": DatasetConfig(
        key="reservoir",
        name="市水务局水库水位表",
        url="https://opendata.sz.gov.cn/api/1952552493/1/service.xhtml",
        output_dir=PROJECT_ROOT / "download" / "市水务局水库水位表",
        csv_basename="市水务局水库水位表_1952552493",
        csv_fields=["测站编码", "自增ID", "时水位（m）", "采集时间"],
        row_mapper=normalize_reservoir_row,
    ),
    "station": DatasetConfig(
        key="station",
        name="市水务局测站基本信息表",
        url="https://opendata.sz.gov.cn/api/1392394662/1/service.xhtml",
        output_dir=PROJECT_ROOT / "download" / "市水务局测站基本信息表",
        csv_basename="市水务局测站基本信息表_1392394662",
        csv_fields=["测站编码", "测站名称", "站类"],
        row_mapper=normalize_station_row,
        include_date_params=False,
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download paginated flooding-point water-level data."
    )
    parser.add_argument(
        "--dataset",
        choices=sorted(DATASETS),
        default="flood",
        help="Dataset to download",
    )
    parser.add_argument(
        "--url",
        default=None,
        help="Override API endpoint URL; normally selected by --dataset",
    )
    parser.add_argument(
        "--app-key",
        default=None,
        help="API appKey. Prefer setting APP_KEY in the environment.",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=DEFAULT_ENV_FILE,
        help="Optional .env file to read APP_KEY from",
    )
    parser.add_argument("--start-date", default="20260601", help="Start date, YYYYMMDD")
    parser.add_argument("--end-date", default="20260623", help="End date, YYYYMMDD")
    parser.add_argument(
        "--months",
        nargs="+",
        default=None,
        help=(
            "Download whole months, such as: --months 202601 202602. "
            "Each month is saved in its own YYYY-MM directory."
        ),
    )
    parser.add_argument("--rows", type=int, default=10000, help="Rows per page")
    parser.add_argument("--page", type=int, default=1, help="First page to request")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Optional page limit for test runs; omit to download all pages",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.2,
        help="Seconds to wait between requests",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Override directory for raw JSON pages and metadata",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Override combined CSV output path",
    )
    return parser.parse_args()


def get_dataset(args: argparse.Namespace) -> DatasetConfig:
    return DATASETS[args.dataset]


def validate_args(args: argparse.Namespace) -> None:
    dataset = get_dataset(args)
    if args.months and not dataset.include_date_params:
        raise ValueError(f"Dataset {dataset.key!r} does not support --months")


def month_date_range(month: str) -> tuple[str, str]:
    if not re.fullmatch(r"\d{6}", month):
        raise ValueError(f"Invalid month {month!r}; expected YYYYMM, such as 202601")

    year = int(month[:4])
    month_number = int(month[4:])
    if month_number < 1 or month_number > 12:
        raise ValueError(f"Invalid month {month!r}; month must be 01-12")

    last_day = calendar.monthrange(year, month_number)[1]
    return f"{year:04d}{month_number:02d}01", f"{year:04d}{month_number:02d}{last_day:02d}"


def month_output_paths(
    base_output_dir: Path, month: str, dataset: DatasetConfig
) -> tuple[Path, Path]:
    if not re.fullmatch(r"\d{6}", month):
        raise ValueError(f"Invalid month {month!r}; expected YYYYMM, such as 202601")

    month_dir_name = f"{month[:4]}-{month[4:]}"
    output_dir = base_output_dir / month_dir_name
    csv_path = output_dir / f"{dataset.csv_basename}_{month}.csv"
    return output_dir, csv_path


def load_app_key(args: argparse.Namespace) -> str | None:
    if args.app_key:
        return args.app_key
    if os.environ.get("APP_KEY"):
        return os.environ["APP_KEY"]
    if not args.env_file.exists():
        return None

    for line in args.env_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        if name.strip() != "APP_KEY":
            continue
        return value.strip().strip("\"'“”‘’")
    return None


def request_page(
    url: str,
    page: int,
    rows: int,
    start_date: str,
    end_date: str,
    app_key: str,
    dataset: DatasetConfig,
) -> dict[str, Any]:
    query = urlencode(
        build_request_params(
            page=page,
            rows=rows,
            start_date=start_date,
            end_date=end_date,
            app_key=app_key,
            dataset=dataset,
        )
    )
    request = Request(
        f"{url}?{query}",
        headers={
            "Accept": "application/json,text/plain,*/*",
            "User-Agent": (
                "Mozilla/5.0 flooding-point-water-level-downloader/1.0 "
                "(local data project)"
            ),
        },
    )
    try:
        with urlopen(request, timeout=60) as response:
            body = response.read()
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {error.code} for page {page}: {body[:500]}") from error
    except URLError as error:
        raise RuntimeError(f"Failed to request page {page}: {error.reason}") from error

    return json.loads(body.decode("utf-8-sig"))


def build_request_params(
    page: int,
    rows: int,
    start_date: str,
    end_date: str,
    app_key: str,
    dataset: DatasetConfig,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "page": page,
        "rows": rows,
        "appKey": app_key,
    }
    if dataset.include_date_params:
        params["startDate"] = start_date
        params["endDate"] = end_date
    return params


def normalize_row(row: dict[str, Any], dataset: DatasetConfig) -> dict[str, Any]:
    return dataset.row_mapper(row)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def clear_existing_raw_pages(raw_dir: Path) -> None:
    if not raw_dir.exists():
        return
    for path in raw_dir.glob("page_*.json"):
        path.unlink()


def download(args: argparse.Namespace) -> tuple[int, int | None]:
    dataset = get_dataset(args)
    url = args.url or dataset.url
    output_dir = args.output_dir or dataset.output_dir
    csv_path = args.csv or output_dir / f"{dataset.csv_basename}.csv"

    app_key = load_app_key(args)
    if not app_key:
        raise ValueError(
            "Missing appKey. Set APP_KEY in the environment, add it to .env, "
            "or pass --app-key."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_dir / "raw_pages"
    raw_dir.mkdir(parents=True, exist_ok=True)
    clear_existing_raw_pages(raw_dir)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    total: int | None = None
    downloaded = 0
    page = args.page
    pages_requested = 0

    with csv_path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=dataset.csv_fields)
        writer.writeheader()

        while True:
            if args.max_pages is not None and pages_requested >= args.max_pages:
                break

            payload = request_page(
                url,
                page,
                args.rows,
                args.start_date,
                args.end_date,
                app_key,
                dataset,
            )
            if payload.get("errorCode"):
                raise RuntimeError(
                    f"API error {payload.get('errorCode')}: {payload.get('message')}"
                )
            pages_requested += 1

            if total is None:
                raw_total = payload.get("total")
                total = int(raw_total) if raw_total not in (None, "") else None

            data = payload.get("data") or []
            if not isinstance(data, list):
                raise ValueError(f"Page {page} returned non-list data: {type(data)!r}")

            write_json(raw_dir / f"page_{page:05d}.json", payload)
            for row in data:
                if not isinstance(row, dict):
                    raise ValueError(f"Page {page} contains a non-object row: {row!r}")
                writer.writerow(normalize_row(row, dataset))

            downloaded += len(data)
            print(f"page={page} rows={len(data)} downloaded={downloaded} total={total}")

            if not data:
                break
            if total is not None and downloaded >= total:
                break
            if len(data) < args.rows:
                break

            page += 1
            if args.sleep:
                time.sleep(args.sleep)

    request_params = build_request_params(
        page=args.page,
        rows=args.rows,
        start_date=args.start_date,
        end_date=args.end_date,
        app_key="(provided; not stored)",
        dataset=dataset,
    )
    metadata = {
        "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dataset": dataset.key,
        "dataset_name": dataset.name,
        "url": url,
        "params": request_params,
        "max_pages": args.max_pages,
        "total_reported_by_api": total,
        "rows_downloaded": downloaded,
        "csv": str(csv_path.resolve()),
        "raw_pages_dir": str(raw_dir.resolve()),
    }
    write_json(output_dir / "download_metadata.json", metadata)
    return downloaded, total


def download_months(args: argparse.Namespace) -> list[tuple[str, int, int | None]]:
    dataset = get_dataset(args)
    base_output_dir = args.output_dir or dataset.output_dir
    results: list[tuple[str, int, int | None]] = []
    for month in args.months:
        start_date, end_date = month_date_range(month)
        output_dir, csv_path = month_output_paths(base_output_dir, month, dataset)
        month_args = argparse.Namespace(**vars(args))
        month_args.start_date = start_date
        month_args.end_date = end_date
        month_args.output_dir = output_dir
        month_args.csv = csv_path

        print(f"month={month} startDate={start_date} endDate={end_date}")
        downloaded, total = download(month_args)
        results.append((month, downloaded, total))
        print(f"Month {month} done. Downloaded {downloaded} rows; API total={total}.")
    return results


def main() -> None:
    args = parse_args()
    validate_args(args)
    if args.months:
        results = download_months(args)
        total_downloaded = sum(downloaded for _, downloaded, _ in results)
        print(f"Done. Downloaded {total_downloaded} rows across {len(results)} months.")
        return

    downloaded, total = download(args)
    print(f"Done. Downloaded {downloaded} rows; API total={total}.")


if __name__ == "__main__":
    main()
