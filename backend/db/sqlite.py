from __future__ import annotations

import sqlite3

from core.config import secrets
from core.security import hash_password


def init_db() -> None:
    conn = sqlite3.connect(secrets.DB_PATH)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role INT NOT NULL DEFAULT 1
            )
            """
        )

        if secrets.ADMIN_USERNAME and secrets.ADMIN_TOKEN:
            hashed_admin_password = hash_password(secrets.ADMIN_TOKEN)
            conn.execute(
                """
                INSERT OR IGNORE INTO users (username, password, role)
                VALUES (?, ?, 2)
                """,
                (secrets.ADMIN_USERNAME, hashed_admin_password),
            )

        conn.commit()
    finally:
        conn.close()
