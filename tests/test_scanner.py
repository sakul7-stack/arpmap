"""Scanner orchestration and export tests, with the ARP table mocked."""

from arpmap import export, scanner
from arpmap.arp import Device


def _fake_devices(*_args, **_kwargs):
    return [
        Device(ip="192.168.1.10", mac="b8:27:eb:fd:de:48"),  # known vendor
        Device(ip="192.168.1.20", mac="de:ad:be:ef:00:01"),  # unknown vendor
    ]


def test_scan_merges_and_stamps(monkeypatch):
    monkeypatch.setattr(scanner.arp, "get_devices", _fake_devices)
    database = {}
    rows = scanner.scan(database, online=False)

    assert len(rows) == 2
    rpi = next(r for r in rows if r.mac == "b8:27:eb:fd:de:48")
    assert rpi.vendor == "Raspberry Pi Foundation"
    assert rpi.first_seen is not None
    # DB was mutated with timestamps.
    assert database["b8:27:eb:fd:de:48"]["last_ip"] == "192.168.1.10"


def test_scan_preserves_existing_name(monkeypatch):
    monkeypatch.setattr(scanner.arp, "get_devices", _fake_devices)
    database = {"b8:27:eb:fd:de:48": {"name": "rpi", "vendor": None,
                                      "last_ip": None, "first_seen": None,
                                      "last_seen": None}}
    rows = scanner.scan(database)
    rpi = next(r for r in rows if r.mac == "b8:27:eb:fd:de:48")
    assert rpi.name == "rpi"


def test_inventory_rows_sorted_by_name():
    database = {
        "aa:aa:aa:aa:aa:aa": {"name": "zebra", "last_ip": "192.168.1.2"},
        "bb:bb:bb:bb:bb:bb": {"name": "alpha", "last_ip": "192.168.1.3"},
    }
    rows = scanner.inventory_rows(database)
    assert [r.name for r in rows] == ["alpha", "zebra"]


def test_export_csv_and_json(monkeypatch):
    monkeypatch.setattr(scanner.arp, "get_devices", _fake_devices)
    rows = scanner.scan({})

    csv_text = export.export(rows, "csv")
    assert "mac,ip,name,hostname,vendor,first_seen,last_seen" in csv_text
    assert "b8:27:eb:fd:de:48" in csv_text

    json_text = export.export(rows, "json")
    assert '"mac": "b8:27:eb:fd:de:48"' in json_text
