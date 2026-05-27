from __future__ import annotations

import logging
import os
import sqlite3
import time
from typing import Any

logger = logging.getLogger("sightlineai.auth")

SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "sightlineai-dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# In-memory user store: user_id -> user dict
_user_store: dict[str, dict[str, Any]] = {}
# Blacklisted tokens
_token_blacklist: set[str] = set()

# Optional SQLite persistence
_DB_PATH = os.getenv("AUTH_DB_PATH", "")


def _get_db() -> sqlite3.Connection | None:
    if not _DB_PATH:
        return None
    try:
        conn = sqlite3.connect(_DB_PATH)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "id TEXT PRIMARY KEY, email TEXT UNIQUE, name TEXT, hashed_password TEXT)"
        )
        return conn
    except Exception:
        return None


def hash_password(password: str) -> str:
    """Hash a password using passlib."""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hash."""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.verify(password, hashed)


def create_token(user_id: str) -> str:
    """Create a JWT token for a user."""
    from jose import jwt
    expire = time.time() + ACCESS_TOKEN_EXPIRE_MINUTES * 60
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict[str, Any] | None:
    """Verify a JWT token. Returns payload or None."""
    if token in _token_blacklist:
        return None
    try:
        from jose import jwt, JWTError
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None


def invalidate_token(token: str) -> None:
    """Add token to blacklist."""
    _token_blacklist.add(token)


def get_user(user_id: str) -> dict[str, Any] | None:
    """Get user by ID."""
    if user_id in _user_store:
        return _user_store[user_id]
    db = _get_db()
    if db:
        try:
            row = db.execute("SELECT id, email, name FROM users WHERE id = ?", (user_id,)).fetchone()
            if row:
                user = {"id": row[0], "email": row[1], "name": row[2]}
                _user_store[user_id] = user
                return user
        finally:
            db.close()
    return None


def register_user(email: str, password: str, name: str) -> dict[str, Any]:
    """Register a new user. Raises ValueError if email exists."""
    from uuid import uuid4

    # Check in-memory
    for user in _user_store.values():
        if user.get("email") == email:
            raise ValueError("Email already registered")

    user_id = str(uuid4())
    hashed = hash_password(password)
    user = {"id": user_id, "email": email, "name": name}

    _user_store[user_id] = user
    _user_store[user_id]["hashed_password"] = hashed

    db = _get_db()
    if db:
        try:
            db.execute("INSERT INTO users (id, email, name, hashed_password) VALUES (?, ?, ?, ?)",
                       (user_id, email, name, hashed))
            db.commit()
        except sqlite3.IntegrityError:
            db.close()
            raise ValueError("Email already registered")
        finally:
            db.close()

    return {"id": user_id, "email": email, "name": name}


def authenticate_user(email: str, password: str) -> dict[str, Any] | None:
    """Authenticate a user. Returns user dict or None."""
    # Check in-memory first
    user_id = None
    hashed_pw = None
    for uid, user in _user_store.items():
        if user.get("email") == email:
            user_id = uid
            hashed_pw = user.get("hashed_password")
            break

    # Check DB
    if not user_id:
        db = _get_db()
        if db:
            try:
                row = db.execute(
                    "SELECT id, email, name, hashed_password FROM users WHERE email = ?", (email,)
                ).fetchone()
                if row:
                    user_id = row[0]
                    hashed_pw = row[3]
                    _user_store[user_id] = {"id": row[0], "email": row[1], "name": row[2], "hashed_password": row[3]}
            finally:
                db.close()

    if not user_id or not hashed_pw:
        return None
    if not verify_password(password, hashed_pw):
        return None
    return {"id": user_id, "email": email, "name": _user_store[user_id].get("name", "")}
