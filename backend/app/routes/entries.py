"""Tracking endpoints: save a footprint entry and list a device's history."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.deps import get_repository
from app.models import Entry, EntryCreate
from app.repository.base import EntryRepository

router = APIRouter(prefix="/api/entries", tags=["entries"])

_DEVICE_ID = Path(min_length=8, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")


@router.post("", response_model=Entry, status_code=201)
async def create_entry(payload: EntryCreate, repo: EntryRepository = Depends(get_repository)) -> Entry:
    """Persist a footprint entry for the (anonymous) device.

    Stores the input snapshot and computed result under the device's anonymous
    identifier. In production this writes to Firestore; locally it uses an
    in-memory store.  Returns 500 if the underlying datastore is unreachable.
    """
    try:
        return await repo.async_add(payload.device_id, payload.input, payload.result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save entry: {exc}") from exc


@router.get("/{device_id}", response_model=list[Entry])
async def list_entries(
    device_id: str = _DEVICE_ID,
    limit: int = Query(50, ge=1, le=200),
    repo: EntryRepository = Depends(get_repository),
) -> list[Entry]:
    """Return a device's footprint history, newest first.

    The limit parameter caps the number of returned entries (default 50,
    maximum 200).  Returns an empty list if the device has no stored entries
    or the store is unavailable.
    """
    try:
        return await repo.async_list_for_device(device_id, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {exc}") from exc
