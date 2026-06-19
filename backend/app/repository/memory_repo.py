"""In-memory EntryRepository for local development and tests.

Thread-safe enough for a single-process dev server; data is ephemeral and lost on
restart. Selected automatically when ``USE_FIRESTORE=false``.

v1.2: added async method wrappers for compatibility with async route handlers.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.models import CarbonInput, Entry, FootprintResult


class InMemoryEntryRepository:
    """EntryRepository backed by a process-local dictionary."""

    def __init__(self) -> None:
        """Start with an empty per-device store."""
        self._by_device: dict[str, list[Entry]] = {}

    def add(self, device_id: str, data: CarbonInput, result: FootprintResult) -> Entry:
        """Persist a new entry for the device and return it with id/timestamp."""
        entry = Entry(
            id=uuid.uuid4().hex,
            created_at=datetime.now(timezone.utc).isoformat(),
            device_id=device_id,
            input=data,
            result=result,
        )
        self._by_device.setdefault(device_id, []).append(entry)
        return entry

    def list_for_device(self, device_id: str, limit: int = 50) -> list[Entry]:
        """Return the device's entries, newest first."""
        entries = self._by_device.get(device_id, [])
        # Newest first.
        return sorted(entries, key=lambda e: e.created_at, reverse=True)[:limit]

    async def async_add(self, device_id: str, data: CarbonInput, result: FootprintResult) -> Entry:
        """Async wrapper — in-memory ops are instant, no thread needed."""
        return self.add(device_id, data, result)

    async def async_list_for_device(self, device_id: str, limit: int = 50) -> list[Entry]:
        """Async wrapper — in-memory ops are instant, no thread needed."""
        return self.list_for_device(device_id, limit=limit)
