"""Vendor/OUI lookup tests (offline only -- no network)."""

from arpmap import vendor


def test_offline_lookup_known_prefix():
    # b8:27:eb is Raspberry Pi Foundation in the bundled table.
    assert vendor.lookup("b8:27:eb:fd:de:48") == "Raspberry Pi Foundation"


def test_offline_lookup_case_insensitive():
    assert vendor.lookup("B8:27:EB:FD:DE:48") == "Raspberry Pi Foundation"


def test_unknown_prefix_offline_returns_none():
    assert vendor.lookup("de:ad:be:ef:00:01", online=False) is None


def test_empty_mac_returns_none():
    assert vendor.lookup("") is None
