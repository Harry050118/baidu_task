from __future__ import annotations

import unittest
from datetime import date

from scripts import audit_downloaded_data as audit


class AuditDownloadedDataTest(unittest.TestCase):
    def test_missing_dates_finds_calendar_gaps(self) -> None:
        observed_dates = {
            date(2026, 1, 1),
            date(2026, 1, 2),
            date(2026, 1, 4),
        }

        self.assertEqual(
            audit.missing_dates(observed_dates, date(2026, 1, 1), date(2026, 1, 4)),
            [date(2026, 1, 3)],
        )

    def test_numeric_summary_tracks_min_max_and_nulls(self) -> None:
        summary = audit.NumericSummary()
        for value in ["", "3.5", "-", "2.0", "bad"]:
            summary.add(value)

        self.assertEqual(summary.total, 5)
        self.assertEqual(summary.numeric_count, 2)
        self.assertEqual(summary.blank_count, 1)
        self.assertEqual(summary.dash_count, 1)
        self.assertEqual(summary.invalid_count, 1)
        self.assertEqual(summary.minimum, 2.0)
        self.assertEqual(summary.maximum, 3.5)


if __name__ == "__main__":
    unittest.main()
