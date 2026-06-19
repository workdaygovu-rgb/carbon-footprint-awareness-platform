"""Tests for the Firestore repository against an in-memory fake client.

The fake mimics the small slice of the Firestore client API the repository
uses (collection/document chaining, ``set``, ``order_by``/``limit``/``stream``)
so the persistence logic is exercised without any network or credentials.
"""

from __future__ import annotations

import pytest
from app.carbon.calculator import calculate_footprint
from app.models import CarbonInput
from app.repository.firestore_repo import FirestoreEntryRepository


class _FakeSnapshot:
    def __init__(self, doc_id, data):
        self.id = doc_id
        self._data = data

    def to_dict(self):
        return self._data


class _FakeQuery:
    def __init__(self, items):
        self._items = items  # list of (doc_id, data)

    def limit(self, n):
        return _FakeQuery(self._items[:n])

    def stream(self):
        return iter(_FakeSnapshot(doc_id, data) for doc_id, data in self._items)


class _FakeEntryDocument:
    def __init__(self, entries, entry_id):
        self._entries = entries
        self._entry_id = entry_id

    def set(self, payload):
        self._entries[self._entry_id] = payload


class _FakeEntriesCollection:
    def __init__(self, entries):
        self._entries = entries  # dict of entry_id -> payload

    def document(self, entry_id):
        return _FakeEntryDocument(self._entries, entry_id)

    def order_by(self, field, direction="ASCENDING"):
        items = sorted(
            self._entries.items(),
            key=lambda kv: kv[1][field],
            reverse=direction == "DESCENDING",
        )
        return _FakeQuery(items)


class _FakeDeviceDocument:
    def __init__(self, store, device_id):
        self._store = store
        self._device_id = device_id

    def collection(self, _name):
        return _FakeEntriesCollection(self._store.setdefault(self._device_id, {}))


class _FakeDevicesCollection:
    def __init__(self, store):
        self._store = store

    def document(self, device_id):
        return _FakeDeviceDocument(self._store, device_id)


class _FakeFirestoreClient:
    def __init__(self, project=None):
        self.project = project
        self._store = {}  # device_id -> {entry_id -> payload}

    def collection(self, _name):
        return _FakeDevicesCollection(self._store)


@pytest.fixture
def repo(monkeypatch):
    monkeypatch.setattr("google.cloud.firestore.Client", _FakeFirestoreClient)
    return FirestoreEntryRepository(project_id="test-project")


def _add(repo, device_id):
    data = CarbonInput()
    return repo.add(device_id, data, calculate_footprint(data))


def test_add_assigns_id_and_utc_timestamp(repo):
    entry = _add(repo, "device-fire-0001")
    assert entry.id
    assert entry.created_at.endswith("+00:00")
    assert entry.device_id == "device-fire-0001"


def test_roundtrip_preserves_input_and_result(repo):
    created = _add(repo, "device-fire-0002")
    [listed] = repo.list_for_device("device-fire-0002")
    assert listed.id == created.id
    assert listed.input == created.input
    assert listed.result == created.result


def test_listing_is_scoped_to_device_and_newest_first(repo):
    first = _add(repo, "device-fire-0003")
    second = _add(repo, "device-fire-0003")
    _add(repo, "device-fire-other")

    entries = repo.list_for_device("device-fire-0003")
    assert [e.id for e in entries] == sorted(
        [first.id, second.id],
        key=lambda i: first.created_at if i == first.id else second.created_at,
        reverse=True,
    )
    assert all(e.device_id == "device-fire-0003" for e in entries)


def test_listing_respects_limit(repo):
    for _ in range(4):
        _add(repo, "device-fire-0004")
    assert len(repo.list_for_device("device-fire-0004", limit=2)) == 2
