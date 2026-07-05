"""Export scan/inventory rows to CSV or JSON."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict
from typing import Sequence

from arpmap.scanner import ScanRow

_FIELDS = ("mac", "ip", "name", "hostname", "vendor", "first_seen", "last_seen")


def to_csv(rows: Sequence[ScanRow]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: (getattr(row, k) or "") for k in _FIELDS})
    return buffer.getvalue()


def to_json(rows: Sequence[ScanRow]) -> str:
    return json.dumps([asdict(row) for row in rows], indent=2) + "\n"


def export(rows: Sequence[ScanRow], fmt: str) -> str:
    """Serialize ``rows`` to ``fmt`` ('csv' or 'json')."""
    fmt = fmt.lower()
    if fmt == "csv":
        return to_csv(rows)
    if fmt == "json":
        return to_json(rows)
    raise ValueError(f"Unknown export format: {fmt!r} (use 'csv' or 'json')")
