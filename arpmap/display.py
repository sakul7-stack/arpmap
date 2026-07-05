"""Table rendering for scan/inventory rows.

Uses ``rich`` if it happens to be installed (nicer colored tables), otherwise
falls back to a dependency-free aligned-columns formatter. Either way the public
function is :func:`render`.
"""

from __future__ import annotations

from typing import Iterable, Sequence

from arpmap.scanner import ScanRow

_COLUMNS: tuple[tuple[str, str], ...] = (
    ("#", "index"),
    ("IP", "ip"),
    ("MAC", "mac"),
    ("Name", "name"),
    ("Hostname", "hostname"),
    ("Vendor", "vendor"),
    ("First seen", "first_seen"),
    ("Last seen", "last_seen"),
)


def _cell(row: ScanRow, field: str, index: int) -> str:
    if field == "index":
        return str(index)
    value = getattr(row, field, None)
    return "-" if value in (None, "") else str(value)


def _render_plain(rows: Sequence[ScanRow]) -> str:
    headers = [title for title, _ in _COLUMNS]
    table = [headers]
    for i, row in enumerate(rows):
        table.append([_cell(row, field, i) for _, field in _COLUMNS])

    widths = [max(len(r[c]) for r in table) for c in range(len(headers))]
    lines = []
    for r_idx, r in enumerate(table):
        line = "  ".join(cell.ljust(widths[c]) for c, cell in enumerate(r))
        lines.append(line.rstrip())
        if r_idx == 0:
            lines.append("  ".join("-" * widths[c] for c in range(len(headers))))
    return "\n".join(lines)


def _render_rich(rows: Sequence[ScanRow]) -> str | None:
    try:
        from rich.console import Console
        from rich.table import Table
    except ImportError:
        return None

    table = Table(show_header=True, header_style="bold cyan")
    for title, _ in _COLUMNS:
        table.add_column(title)
    for i, row in enumerate(rows):
        table.add_row(*[_cell(row, field, i) for _, field in _COLUMNS])

    console = Console()
    with console.capture() as capture:
        console.print(table)
    return capture.get()


def render(rows: Iterable[ScanRow], *, use_rich: bool = True) -> str:
    """Return a printable table for ``rows``."""
    rows = list(rows)
    if not rows:
        return "No devices found."
    if use_rich:
        rich_out = _render_rich(rows)
        if rich_out is not None:
            return rich_out.rstrip("\n")
    return _render_plain(rows)
