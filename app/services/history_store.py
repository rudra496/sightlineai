from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas import GuidanceResponse, SessionHistoryItem


class SessionHistoryStore:
    def __init__(self, max_items: int = 100) -> None:
        self._items: deque[SessionHistoryItem] = deque(maxlen=max_items)

    def add_from_guidance(self, source: str, scene: str, response: GuidanceResponse, pinned: bool = False) -> SessionHistoryItem:
        item = SessionHistoryItem(
            id=str(uuid4()),
            created_at=datetime.now(timezone.utc).isoformat(),
            source=source,
            scene_description=scene,
            guidance=response,
            pinned=pinned,
        )
        self._items.appendleft(item)
        return item

    def add_item(self, item: SessionHistoryItem) -> SessionHistoryItem:
        self._items.appendleft(item)
        return item

    def list_items(self) -> list[SessionHistoryItem]:
        return list(self._items)

    def clear(self) -> None:
        self._items.clear()
