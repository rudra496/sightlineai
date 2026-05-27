from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from app.schemas import GuidanceResponse, SessionHistoryItem


class SessionHistoryStore:
    def __init__(self, max_items: int = 100) -> None:
        self._items: deque[SessionHistoryItem] = deque(maxlen=max_items)
        self._max_items = max_items

    def add_from_guidance(self, source: str, scene: str, response: GuidanceResponse, pinned: bool = False, favorite: bool = False) -> SessionHistoryItem:
        item = SessionHistoryItem(
            id=str(uuid4()),
            created_at=datetime.now(timezone.utc).isoformat(),
            source=source,
            scene_description=scene,
            guidance=response,
            pinned=pinned,
            favorite=favorite,
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

    def get_by_id(self, item_id: str) -> SessionHistoryItem | None:
        for item in self._items:
            if item.id == item_id:
                return item
        return None

    def delete(self, item_id: str) -> bool:
        for item in self._items:
            if item.id == item_id:
                self._items.remove(item)
                return True
        return False

    def search(
        self,
        source: str | None = None,
        keyword: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[SessionHistoryItem]:
        results = list(self._items)
        if source:
            results = [item for item in results if item.source == source]
        if keyword:
            kw_lower = keyword.lower()
            results = [
                item for item in results
                if kw_lower in item.scene_description.lower()
                or kw_lower in item.guidance.guidance_text.lower()
                or kw_lower in item.guidance.safety_notes.lower()
            ]
        if date_from:
            results = [item for item in results if item.created_at >= date_from]
        if date_to:
            results = [item for item in results if item.created_at <= date_to]
        return results

    def pin(self, item_id: str) -> SessionHistoryItem | None:
        for item in self._items:
            if item.id == item_id:
                pinned_item = item.model_copy(update={"pinned": True})
                self._items.remove(item)
                new_items = [pinned_item] + [i for i in self._items if i.id != item_id]
                self._items.clear()
                for i in new_items:
                    self._items.append(i)
                return pinned_item
        return None

    def unpin(self, item_id: str) -> SessionHistoryItem | None:
        for item in self._items:
            if item.id == item_id:
                unpinned_item = item.model_copy(update={"pinned": False})
                self._items.remove(item)
                self._items.appendleft(unpinned_item)
                return unpinned_item
        return None

    def favorite(self, item_id: str) -> SessionHistoryItem | None:
        for item in self._items:
            if item.id == item_id:
                fav_item = item.model_copy(update={"favorite": True})
                self._items.remove(item)
                self._items.appendleft(fav_item)
                return fav_item
        return None

    def unfavorite(self, item_id: str) -> SessionHistoryItem | None:
        for item in self._items:
            if item.id == item_id:
                unfav_item = item.model_copy(update={"favorite": False})
                self._items.remove(item)
                self._items.appendleft(unfav_item)
                return unfav_item
        return None

    def export_all(self) -> list[dict]:
        return [item.model_dump() for item in self._items]

    def get_config(self) -> dict:
        return {"max_items": self._max_items, "current_count": len(self._items)}

    def set_max_items(self, max_items: int) -> None:
        if max_items < 1:
            return
        self._max_items = max_items
        items = list(self._items)
        self._items = deque(items[:max_items], maxlen=max_items)
