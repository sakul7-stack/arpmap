"""Stats summary tests."""

from arpmap import stats


def _db():
    return {
        "aa:aa:aa:aa:aa:aa": {"name": "nas", "vendor": "Synology", "hostname": "nas.lan"},
        "bb:bb:bb:bb:bb:bb": {"name": "pi", "vendor": "Raspberry Pi Foundation"},
        "cc:cc:cc:cc:cc:cc": {"name": None, "vendor": "Raspberry Pi Foundation"},
        "dd:dd:dd:dd:dd:dd": {"name": None, "vendor": None},
    }


def test_summarize_counts():
    s = stats.summarize(_db())
    assert s["total"] == 4
    assert s["named"] == 2
    assert s["unnamed"] == 2
    assert s["with_hostname"] == 1
    assert s["with_vendor"] == 3


def test_summarize_vendor_breakdown():
    s = stats.summarize(_db())
    vendors = dict(s["vendors"])
    assert vendors["Raspberry Pi Foundation"] == 2
    assert vendors["Synology"] == 1
    assert vendors["Unknown"] == 1


def test_render_empty():
    assert "No devices" in stats.render({})


def test_render_nonempty():
    out = stats.render(_db())
    assert "Total devices : 4" in out
    assert "Raspberry Pi Foundation" in out
