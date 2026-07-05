"""Summary statistics over the device database."""

from __future__ import annotations

from collections import Counter
from typing import Any


def summarize(database: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Compute headline numbers and a vendor breakdown for ``database``."""
    total = len(database)
    named = sum(1 for r in database.values() if r.get("name"))
    with_hostname = sum(1 for r in database.values() if r.get("hostname"))
    with_vendor = sum(1 for r in database.values() if r.get("vendor"))

    vendors = Counter(
        r.get("vendor") or "Unknown" for r in database.values()
    )
    return {
        "total": total,
        "named": named,
        "unnamed": total - named,
        "with_hostname": with_hostname,
        "with_vendor": with_vendor,
        "vendors": vendors.most_common(),
    }


def render(database: dict[str, dict[str, Any]]) -> str:
    """Human-readable stats block."""
    s = summarize(database)
    if s["total"] == 0:
        return "No devices recorded yet. Run a scan first."

    lines = [
        "Network summary",
        "===============",
        f"Total devices : {s['total']}",
        f"Named         : {s['named']}",
        f"Unnamed       : {s['unnamed']}",
        f"With hostname : {s['with_hostname']}",
        f"With vendor   : {s['with_vendor']}",
        "",
        "Top vendors",
        "-----------",
    ]
    for vendor, count in s["vendors"][:10]:
        lines.append(f"{count:>3}  {vendor}")
    return "\n".join(lines)
