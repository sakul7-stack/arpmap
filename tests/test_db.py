"""Database load/save/migration tests."""

import json

from arpmap import db


def test_load_missing_returns_empty(tmp_path):
    assert db.load_db(str(tmp_path / "nope.json")) == {}


def test_migrates_flat_format(tmp_path):
    path = tmp_path / "old.json"
    path.write_text(json.dumps({"E0-DB-55-D6-ED-16": "arch-laptop"}))

    loaded = db.load_db(str(path))
    # Key normalized to lowercase, value expanded to a full record.
    record = loaded["e0-db-55-d6-ed-16"]
    assert record["name"] == "arch-laptop"
    assert record["vendor"] is None
    assert record["first_seen"] is None


def test_touch_sets_first_seen_once(tmp_path):
    database = {}
    r1 = db.touch(database, "aa:bb:cc:dd:ee:ff", ip="192.168.1.5", timestamp="2026-01-01T00:00:00")
    r2 = db.touch(database, "aa:bb:cc:dd:ee:ff", ip="192.168.1.6", timestamp="2026-02-02T00:00:00")
    assert r1 is r2
    assert r2["first_seen"] == "2026-01-01T00:00:00"
    assert r2["last_seen"] == "2026-02-02T00:00:00"
    assert r2["last_ip"] == "192.168.1.6"


def test_touch_does_not_clobber_vendor(tmp_path):
    database = {}
    db.touch(database, "aa:bb:cc:dd:ee:ff", vendor="Acme")
    db.touch(database, "aa:bb:cc:dd:ee:ff", vendor=None)
    assert database["aa:bb:cc:dd:ee:ff"]["vendor"] == "Acme"


def test_roundtrip_save_load(tmp_path):
    path = str(tmp_path / "db.json")
    database = {}
    db.touch(database, "aa:bb:cc:dd:ee:ff", ip="192.168.1.5", timestamp="2026-01-01T00:00:00")
    db.save_db(database, path)
    reloaded = db.load_db(path)
    assert reloaded == database


def test_find_mac_by_ip_and_mac():
    database = {"aa:bb:cc:dd:ee:ff": {"last_ip": "192.168.1.9", "name": "x"}}
    assert db.find_mac(database, "192.168.1.9") == "aa:bb:cc:dd:ee:ff"
    assert db.find_mac(database, "AA-BB-CC-DD-EE-FF") == "aa:bb:cc:dd:ee:ff"
    assert db.find_mac(database, "10.0.0.1") is None
