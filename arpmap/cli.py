"""Command-line interface for ARPMap.

Subcommands:
    scan    Discover devices on the network (default) and show a table.
    list    Show the stored inventory without scanning.
    name    Assign names to devices (interactive, or one-shot ``name <id> <name>``).
    watch   Continuously re-scan and report new/departed devices.
    export  Write the current inventory to CSV or JSON.
"""

from __future__ import annotations

import argparse
import sys
import time

from arpmap import __version__, db, display, export as export_mod, scanner
from arpmap.arp import normalize_mac


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _print_rows(rows, use_rich: bool = True) -> None:
    print()
    print(display.render(rows, use_rich=use_rich))
    print()


def _prompt(text: str) -> str:
    try:
        return input(text).strip()
    except EOFError:
        return ""


# --------------------------------------------------------------------------- #
# scan
# --------------------------------------------------------------------------- #
def cmd_scan(args: argparse.Namespace) -> int:
    database = db.load_db(args.db)
    rows = scanner.scan(
        database,
        do_sweep=args.sweep,
        online=args.online,
        only_private=not args.all,
    )
    db.save_db(database, args.db)
    if args.sweep:
        print("Ping sweep complete.")
    _print_rows(rows, use_rich=not args.plain)

    if args.name:
        _interactive_name(database, rows, args.db)
    return 0


# --------------------------------------------------------------------------- #
# list
# --------------------------------------------------------------------------- #
def cmd_list(args: argparse.Namespace) -> int:
    database = db.load_db(args.db)
    rows = scanner.inventory_rows(database)
    _print_rows(rows, use_rich=not args.plain)
    return 0


# --------------------------------------------------------------------------- #
# name
# --------------------------------------------------------------------------- #
def _interactive_name(database, rows, db_path) -> None:
    """Original interactive naming flow, preserved and re-used by scan/name."""
    if not rows:
        print("Nothing to name.")
        return
    while True:
        nums = _prompt("Enter device number(s) to name (comma separated, blank to stop): ")
        if not nums:
            break
        for token in nums.split(","):
            token = token.strip()
            if not token:
                continue
            try:
                idx = int(token)
                row = rows[idx]
            except (ValueError, IndexError):
                print(f"Invalid selection: {token}")
                continue
            name = _prompt(f"Enter name for {row.ip} ({row.mac}): ")
            if name:
                db.record_for(database, row.mac)["name"] = name
                row.name = name
                print(f"Saved: {name}")
        if _prompt("Add another device? (Y/n): ").lower() == "n":
            break
    db.save_db(database, db_path)
    print("All changes saved.")


def cmd_name(args: argparse.Namespace) -> int:
    database = db.load_db(args.db)

    # One-shot form: `arpmap name <mac|ip> <name>`
    if args.target is not None:
        mac = db.find_mac(database, args.target) or normalize_mac(args.target)
        db.record_for(database, mac)["name"] = args.new_name
        db.save_db(database, args.db)
        print(f"Named {mac} -> {args.new_name}")
        return 0

    # Interactive form: scan first so there is something to select.
    rows = scanner.scan(database, only_private=not args.all)
    db.save_db(database, args.db)
    _print_rows(rows, use_rich=not args.plain)
    _interactive_name(database, rows, args.db)
    return 0


# --------------------------------------------------------------------------- #
# watch
# --------------------------------------------------------------------------- #
def cmd_watch(args: argparse.Namespace) -> int:
    database = db.load_db(args.db)
    previous: dict[str, str] = {}  # mac -> ip
    first = True
    print(f"Watching network every {args.interval}s (Ctrl-C to stop)...\n")
    try:
        while True:
            rows = scanner.scan(
                database,
                do_sweep=args.sweep,
                online=args.online,
                only_private=not args.all,
            )
            db.save_db(database, args.db)
            current = {r.mac: r.ip for r in rows}
            label = {r.mac: (r.name or r.vendor or r.mac) for r in rows}

            if first:
                print(f"[{db.now_iso()}] {len(rows)} device(s) present.")
                first = False
            else:
                for mac, ip in current.items():
                    if mac not in previous:
                        print(f"[{db.now_iso()}] NEW    {ip:15} {label[mac]}")
                    elif previous[mac] != ip:
                        print(
                            f"[{db.now_iso()}] IP-CHG {previous[mac]} -> {ip} "
                            f"{label[mac]}"
                        )
                for mac, ip in previous.items():
                    if mac not in current:
                        print(f"[{db.now_iso()}] GONE   {ip:15} {mac}")

            previous = current
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


# --------------------------------------------------------------------------- #
# export
# --------------------------------------------------------------------------- #
def cmd_export(args: argparse.Namespace) -> int:
    database = db.load_db(args.db)
    if args.scan:
        rows = scanner.scan(database, do_sweep=args.sweep, only_private=not args.all)
        db.save_db(database, args.db)
    else:
        rows = scanner.inventory_rows(database)

    text = export_mod.export(rows, args.format)
    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        print(f"Wrote {len(rows)} row(s) to {args.output}")
    else:
        sys.stdout.write(text)
    return 0


# --------------------------------------------------------------------------- #
# argument parsing
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="arpmap",
        description="Discover, name, and track devices on your local network.",
    )
    parser.add_argument("--version", action="version", version=f"arpmap {__version__}")
    parser.add_argument(
        "--db",
        default=db.DEFAULT_DB_FILE,
        help=f"Path to the device database (default: {db.DEFAULT_DB_FILE})",
    )
    parser.add_argument(
        "--plain", action="store_true", help="Force plain-text tables (no rich)."
    )

    sub = parser.add_subparsers(dest="command")

    # scan (default)
    p_scan = sub.add_parser("scan", help="Scan the network and show devices.")
    p_scan.add_argument("--sweep", action="store_true", help="Ping-sweep the subnet first.")
    p_scan.add_argument("--online", action="store_true", help="Allow online vendor lookups.")
    p_scan.add_argument("--all", action="store_true", help="Include non-private IPs.")
    p_scan.add_argument("--name", action="store_true", help="Name devices after scanning.")
    p_scan.set_defaults(func=cmd_scan)

    # list
    p_list = sub.add_parser("list", help="Show stored inventory without scanning.")
    p_list.set_defaults(func=cmd_list)

    # name
    p_name = sub.add_parser("name", help="Assign names to devices.")
    p_name.add_argument("target", nargs="?", help="MAC or IP to name (one-shot form).")
    p_name.add_argument("new_name", nargs="?", help="Name to assign (one-shot form).")
    p_name.add_argument("--all", action="store_true", help="Include non-private IPs.")
    p_name.set_defaults(func=cmd_name)

    # watch
    p_watch = sub.add_parser("watch", help="Continuously monitor for device changes.")
    p_watch.add_argument("--interval", type=int, default=10, help="Seconds between scans.")
    p_watch.add_argument("--sweep", action="store_true", help="Ping-sweep each cycle.")
    p_watch.add_argument("--online", action="store_true", help="Allow online vendor lookups.")
    p_watch.add_argument("--all", action="store_true", help="Include non-private IPs.")
    p_watch.set_defaults(func=cmd_watch)

    # export
    p_export = sub.add_parser("export", help="Export inventory to CSV or JSON.")
    p_export.add_argument("--format", choices=("csv", "json"), default="csv")
    p_export.add_argument("--output", "-o", help="Output file (default: stdout).")
    p_export.add_argument("--scan", action="store_true", help="Scan first, then export.")
    p_export.add_argument("--sweep", action="store_true", help="Ping-sweep before scanning.")
    p_export.add_argument("--all", action="store_true", help="Include non-private IPs.")
    p_export.set_defaults(func=cmd_export)

    return parser


def main(argv: list[str] | None = None) -> int:
    raw = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    args = parser.parse_args(raw)

    # Default to `scan` when no subcommand is given.
    if args.command is None:
        args = parser.parse_args(raw + ["scan"])

    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"Required command not found: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - top-level guard for a CLI
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
