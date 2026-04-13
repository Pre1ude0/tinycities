from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Optional
from core.config import secrets


@dataclass()
class UserRecord:
    id: int
    username: str
    role: int


def username_exists(conn: sqlite3.Connection, username: str) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE username = ? LIMIT 1", (username,))
    return cur.fetchone() is not None


def create_user(conn: sqlite3.Connection, username: str, password_hash: str, role: int = 1) -> int:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
        (username, password_hash, int(role)),
    )
    if cur.rowcount == 0 or cur.lastrowid is None:
        raise Exception("Failed to create user")
    return int(cur.lastrowid)

def bootstrap_admin_user(conn: sqlite3.Connection, username: str, password_hash: str) -> None:
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, 2)",
        (username, password_hash),
    )

def parse_payload(payload: dict) -> Optional[UserRecord]:
    required_fields = UserRecord.__dataclass_fields__.keys()
    if not all(field in payload for field in required_fields):
        return None
    try:
        return UserRecord(
            id=int(payload["id"]),
            username=str(payload["username"]),
            role=int(payload["role"]),
        )
    except (ValueError, TypeError):
        return None

def update_user(conn: sqlite3.Connection, user_id: int, **kwargs) -> bool:
    cur = conn.cursor()
    set_clause = ", ".join(f"{key} = ?" for key in kwargs)
    values = list(kwargs.values()) + [user_id]
    cur.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
    return cur.rowcount > 0
