from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

logger = logging.getLogger("sightlineai.persistence")

DB_PATH = os.getenv("SQLITE_DB_PATH", "sightlineai.db")


def _get_db_path() -> str:
    """Resolve DB path relative to the app root."""
    p = Path(DB_PATH)
    if not p.is_absolute():
        p = Path(__file__).resolve().parent.parent.parent / p
    return str(p)


def init_db(db_path: str | None = None) -> sqlite3.Connection:
    """Initialize SQLite database with required tables."""
    path = db_path or _get_db_path()
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS history (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            source TEXT NOT NULL,
            scene_description TEXT NOT NULL,
            guidance_json TEXT NOT NULL,
            pinned INTEGER DEFAULT 0,
            favorite INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS conversations (
            session_id TEXT PRIMARY KEY,
            messages_json TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)
    conn.commit()
    logger.info("SQLite database initialized at %s", path)
    return conn


class SQLiteStore:
    """SQLite-backed storage for history, conversations, and settings."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    # --- History ---

    def add_history_item(self, item_id: str, created_at: str, source: str,
                         scene_description: str, guidance: dict, pinned: bool = False,
                         favorite: bool = False) -> None:
        self._conn.execute(
            "INSERT INTO history (id, created_at, source, scene_description, guidance_json, pinned, favorite) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (item_id, created_at, source, scene_description, json.dumps(guidance), int(pinned), int(favorite)),
        )
        self._conn.commit()

    def list_history(self) -> list[dict]:
        rows = self._conn.execute("SELECT * FROM history ORDER BY created_at DESC").fetchall()
        return [self._row_to_history(dict(r)) for r in rows]

    def get_history_item(self, item_id: str) -> dict | None:
        row = self._conn.execute("SELECT * FROM history WHERE id = ?", (item_id,)).fetchone()
        if not row:
            return None
        return self._row_to_history(dict(row))

    def delete_history_item(self, item_id: str) -> bool:
        cursor = self._conn.execute("DELETE FROM history WHERE id = ?", (item_id,))
        self._conn.commit()
        return cursor.rowcount > 0

    def clear_history(self) -> None:
        self._conn.execute("DELETE FROM history")
        self._conn.commit()

    def pin_history_item(self, item_id: str, pinned: bool = True) -> dict | None:
        row = self.get_history_item(item_id)
        if not row:
            return None
        self._conn.execute("UPDATE history SET pinned = ? WHERE id = ?", (int(pinned), item_id))
        self._conn.commit()
        row["pinned"] = pinned
        return row

    def favorite_history_item(self, item_id: str, favorite: bool = True) -> dict | None:
        row = self.get_history_item(item_id)
        if not row:
            return None
        self._conn.execute("UPDATE history SET favorite = ? WHERE id = ?", (int(favorite), item_id))
        self._conn.commit()
        row["favorite"] = favorite
        return row

    def list_favorites(self) -> list[dict]:
        rows = self._conn.execute("SELECT * FROM history WHERE favorite = 1 ORDER BY created_at DESC").fetchall()
        return [self._row_to_history(dict(r)) for r in rows]

    def search_history(self, source: str | None = None, keyword: str | None = None,
                       date_from: str | None = None, date_to: str | None = None) -> list[dict]:
        query = "SELECT * FROM history WHERE 1=1"
        params: list[Any] = []
        if source:
            query += " AND source = ?"
            params.append(source)
        if keyword:
            query += " AND (scene_description LIKE ? OR guidance_json LIKE ?)"
            kw = f"%{keyword}%"
            params.extend([kw, kw])
        if date_from:
            query += " AND created_at >= ?"
            params.append(date_from)
        if date_to:
            query += " AND created_at <= ?"
            params.append(date_to)
        query += " ORDER BY created_at DESC"
        rows = self._conn.execute(query, params).fetchall()
        return [self._row_to_history(dict(r)) for r in rows]

    # --- Conversations ---

    def save_conversation(self, session_id: str, messages: list[dict], created_at: str, updated_at: str) -> None:
        existing = self._conn.execute("SELECT session_id FROM conversations WHERE session_id = ?", (session_id,)).fetchone()
        if existing:
            self._conn.execute(
                "UPDATE conversations SET messages_json = ?, updated_at = ? WHERE session_id = ?",
                (json.dumps(messages), updated_at, session_id),
            )
        else:
            self._conn.execute(
                "INSERT INTO conversations (session_id, messages_json, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (session_id, json.dumps(messages), created_at, updated_at),
            )
        self._conn.commit()

    def get_conversation(self, session_id: str) -> dict | None:
        row = self._conn.execute("SELECT * FROM conversations WHERE session_id = ?", (session_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["messages"] = json.loads(d["messages_json"])
        return d

    def delete_conversation(self, session_id: str) -> bool:
        cursor = self._conn.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
        self._conn.commit()
        return cursor.rowcount > 0

    # --- Settings ---

    def get_setting(self, key: str) -> str | None:
        row = self._conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None

    def set_setting(self, key: str, value: str) -> None:
        self._conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = ?",
            (key, value, value),
        )
        self._conn.commit()

    # --- Helpers ---

    @staticmethod
    def _row_to_history(row: dict) -> dict:
        row["guidance"] = json.loads(row.pop("guidance_json"))
        row["pinned"] = bool(row.get("pinned", 0))
        row["favorite"] = bool(row.get("favorite", 0))
        return row
