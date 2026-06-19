"""Firestore-backed EntryRepository (Google Cloud Native mode).

Entries are stored anonymously under ``devices/{device_id}/entries/{id}`` —
keyed by a client-generated random device id, so no personal account or login is
required. Authentication is via Application Default Credentials (the Cloud Run
service account), so there is no credential file in the codebase.

The Firestore client is imported lazily so that importing this module never
requires the dependency or credentials until the backend is actually selected.

v1.2: added async variants using asyncio.to_thread for the synchronous Firestore
client (the async Firestore client API mirrors the sync one but is not always
available in all environments, so wrapping in to_thread is the safer approach).
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from app.models import CarbonInput, Entry, FootprintResult

_COLLECTION = "devices"
_SUBCOLLECTION = "entries"


class FirestoreEntryRepository:
    """EntryRepository backed by Firestore subcollections per device."""

    def __init__(self, project_id: str) -> None:
        """Create a Firestore client for the given project (auth via ADC)."""
        from google.cloud import firestore  # lazy import

        self._db = firestore.Client(project=project_id)

    def add(self, device_id: str, data: CarbonInput, result: FootprintResult) -> Entry:
        """Persist a new entry under the device and return it with id/timestamp."""
        entry_id = uuid.uuid4().hex
        created_at = datetime.now(timezone.utc).isoformat()
        doc = (
            self._db.collection(_COLLECTION)
            .document(device_id)
            .collection(_SUBCOLLECTION)
            .document(entry_id)
        )
        doc.set(
            {
                "created_at": created_at,
                "input": data.model_dump(mode="json"),
                "result": result.model_dump(mode="json"),
            }
        )
        return Entry(
            id=entry_id,
            created_at=created_at,
            device_id=device_id,
            input=data,
            result=result,
        )

    def list_for_device(self, device_id: str, limit: int = 50) -> list[Entry]:
        """Return the device's entries, newest first."""
        from google.cloud import firestore  # lazy import

        snapshots = (
            self._db.collection(_COLLECTION)
            .document(device_id)
            .collection(_SUBCOLLECTION)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
        entries: list[Entry] = []
        for snap in snapshots:
            raw = snap.to_dict()
            entries.append(
                Entry(
                    id=snap.id,
                    created_at=raw["created_at"],
                    device_id=device_id,
                    input=CarbonInput.model_validate(raw["input"]),
                    result=FootprintResult.model_validate(raw["result"]),
                )
            )
        return entries

    async def async_add(self, device_id: str, data: CarbonInput, result: FootprintResult) -> Entry:
        """Async variant — runs the sync Firestore call in a thread pool."""
        return await asyncio.to_thread(self.add, device_id, data, result)

    async def async_list_for_device(self, device_id: str, limit: int = 50) -> list[Entry]:
        """Async variant — runs the sync Firestore call in a thread pool."""
        return await asyncio.to_thread(self.list_for_device, device_id, limit)
