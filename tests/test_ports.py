"""Port-scanner helper tests (no live network dependency)."""

from arpmap import ports


def test_parse_ports_single_and_list():
    assert ports.parse_ports("22") == [22]
    assert ports.parse_ports("22,80,443") == [22, 80, 443]


def test_parse_ports_range():
    assert ports.parse_ports("80-83") == [80, 81, 82, 83]


def test_parse_ports_dedupes_and_sorts():
    assert ports.parse_ports("443,80,80,22") == [22, 80, 443]


def test_parse_ports_ignores_out_of_range():
    assert ports.parse_ports("0,22,70000") == [22]


def test_service_name():
    assert ports.service_name(22) == "ssh"
    assert ports.service_name(443) == "https"
    assert ports.service_name(12345) == "?"


def test_scan_host_uses_check_port(monkeypatch):
    # Pretend only port 80 is open; verify scan_host reports (80, 'http').
    monkeypatch.setattr(ports, "check_port", lambda ip, port, timeout: port == 80)
    result = ports.scan_host("192.168.1.1", [22, 80, 443])
    assert result == [(80, "http")]
