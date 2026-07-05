"""Hostname resolution tests with the resolver mocked (no real DNS)."""

import socket

from arpmap import hostname


def test_resolve_success(monkeypatch):
    monkeypatch.setattr(
        hostname.socket, "gethostbyaddr", lambda ip: ("nas.lan", [], [ip])
    )
    assert hostname.resolve("192.168.1.10") == "nas.lan"


def test_resolve_strips_trailing_dot(monkeypatch):
    monkeypatch.setattr(
        hostname.socket, "gethostbyaddr", lambda ip: ("router.lan.", [], [ip])
    )
    assert hostname.resolve("192.168.1.1") == "router.lan"


def test_resolve_failure_returns_none(monkeypatch):
    def boom(ip):
        raise socket.herror()

    monkeypatch.setattr(hostname.socket, "gethostbyaddr", boom)
    assert hostname.resolve("192.168.1.99") is None


def test_resolve_bare_ip_answer_is_none(monkeypatch):
    monkeypatch.setattr(
        hostname.socket, "gethostbyaddr", lambda ip: (ip, [], [ip])
    )
    assert hostname.resolve("192.168.1.5") is None


def test_resolve_many_empty():
    assert hostname.resolve_many([]) == {}


def test_resolve_many(monkeypatch):
    monkeypatch.setattr(
        hostname.socket, "gethostbyaddr", lambda ip: (f"host-{ip}", [], [ip])
    )
    result = hostname.resolve_many(["192.168.1.1", "192.168.1.2"])
    assert result == {
        "192.168.1.1": "host-192.168.1.1",
        "192.168.1.2": "host-192.168.1.2",
    }
