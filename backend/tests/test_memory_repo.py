"""Tests for the in-memory entry repository."""

from __future__ import annotations

from app.carbon.calculator import calculate_footprint
from app.models import CarbonInput
from app.repository.memory_repo import InMemoryEntryRepository


def _make(repo, device_id):
    data = CarbonInput()
    return repo.add(device_id, data, calculate_footprint(data))


def test_add_returns_entry_with_id_and_timestamp():
    repo = InMemoryEntryRepository()
    entry = _make(repo, "device-abc123")
    assert entry.id
    assert entry.created_at
    assert entry.device_id == "device-abc123"


def test_list_is_scoped_to_device():
    repo = InMemoryEntryRepository()
    _make(repo, "device-aaaa1111")
    _make(repo, "device-bbbb2222")
    assert len(repo.list_for_device("device-aaaa1111")) == 1
    assert len(repo.list_for_device("device-bbbb2222")) == 1
    assert repo.list_for_device("device-unknown99") == []


def test_list_respects_limit():
    repo = InMemoryEntryRepository()
    for _ in range(5):
        _make(repo, "device-cccc3333")
    assert len(repo.list_for_device("device-cccc3333", limit=3)) == 3


def test_list_returns_newest_first(monkeypatch):
    from datetime import datetime

    ticks = iter(range(1, 10))

    class _TickingDatetime:
        @staticmethod
        def now(tz=None):
            return datetime(2026, 1, 1, 0, 0, next(ticks), tzinfo=tz)

    monkeypatch.setattr("app.repository.memory_repo.datetime", _TickingDatetime)
    repo = InMemoryEntryRepository()
    first = _make(repo, "device-dddd4444")
    second = _make(repo, "device-dddd4444")
    third = _make(repo, "device-dddd4444")

    listed = repo.list_for_device("device-dddd4444")
    assert [e.id for e in listed] == [third.id, second.id, first.id]
