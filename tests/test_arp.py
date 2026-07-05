"""Parser tests using captured ``arp -a`` output from each platform."""

from arpmap.arp import (
    is_private_ipv4,
    normalize_mac,
    parse_arp_output,
)

WINDOWS_OUTPUT = """
Interface: 192.168.1.48 --- 0x11
  Internet Address      Physical Address      Type
  192.168.1.1           d8-4a-2b-3e-16-f0     dynamic
  192.168.1.10          2c-cf-67-da-bd-80     dynamic
  192.168.1.255         ff-ff-ff-ff-ff-ff     static
  224.0.0.22            01-00-5e-00-00-16     static
"""

LINUX_OUTPUT = """
? (192.168.1.1) at d8:4a:2b:3e:16:f0 [ether] on eth0
? (192.168.1.10) at 2c:cf:67:da:bd:80 [ether] on eth0
? (10.0.0.5) at aa:bb:cc:dd:ee:01 [ether] on wlan0
"""

MACOS_OUTPUT = """
router.lan (192.168.1.1) at d8:4a:2b:3e:16:f0 on en0 ifscope [ethernet]
? (192.168.1.10) at 2c:cf:67:da:bd:80 on en0 ifscope [ethernet]
? (224.0.0.251) at 1:0:5e:0:0:fb on en0 ifscope permanent [ethernet]
"""


def test_normalize_mac():
    assert normalize_mac("D8-4A-2B-3E-16-F0") == "d8:4a:2b:3e:16:f0"
    assert normalize_mac("AA:BB:CC:DD:EE:FF") == "aa:bb:cc:dd:ee:ff"


def test_is_private_ipv4():
    assert is_private_ipv4("192.168.1.1")
    assert is_private_ipv4("10.0.0.5")
    assert is_private_ipv4("172.16.0.1")
    assert is_private_ipv4("172.31.255.255")
    # 172.32 is outside the /12 range -- the original startswith("172.") bug.
    assert not is_private_ipv4("172.32.0.1")
    assert not is_private_ipv4("8.8.8.8")
    assert not is_private_ipv4("nonsense")


def test_windows_parse():
    devices = parse_arp_output(WINDOWS_OUTPUT)
    macs = {d.mac for d in devices}
    assert macs == {"d8:4a:2b:3e:16:f0", "2c:cf:67:da:bd:80"}  # bcast/mcast dropped


def test_linux_parse_matches_windows_normalization():
    devices = parse_arp_output(LINUX_OUTPUT)
    by_ip = {d.ip: d.mac for d in devices}
    assert by_ip["192.168.1.1"] == "d8:4a:2b:3e:16:f0"
    assert by_ip["10.0.0.5"] == "aa:bb:cc:dd:ee:01"


def test_macos_drops_multicast():
    devices = parse_arp_output(MACOS_OUTPUT)
    ips = {d.ip for d in devices}
    assert "224.0.0.251" not in ips
    assert "192.168.1.1" in ips


def test_all_flag_keeps_public_ips():
    output = "? (8.8.8.8) at aa:bb:cc:dd:ee:ff on en0"
    assert parse_arp_output(output, only_private=True) == []
    assert len(parse_arp_output(output, only_private=False)) == 1


def test_dedupes_by_mac():
    output = """
    192.168.1.1  aa-bb-cc-dd-ee-ff dynamic
    192.168.1.2  aa-bb-cc-dd-ee-ff dynamic
    """
    assert len(parse_arp_output(output)) == 1
