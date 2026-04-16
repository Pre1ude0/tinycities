from __future__ import annotations

import sqlite3

from core.secrets import secrets
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
                (secrets.ADMIN_USERNAME, hashed_admin_password)
            )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                is_private BOOL NOT NULL DEFAULT 0,
                external_url TEXT UNIQUE,
                CHECK (name IS NOT NULL OR external_url IS NOT NULL)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS access (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                page_id INTEGER NOT NULL,
                role INT NOT NULL DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (page_id) REFERENCES pages (id)
            )
            """
        )

        # conn.execute(
        #     """
        #     CREATE TABLE IF NOT EXISTS changes  (
        #         id INTEGER PRIMARY KEY AUTOINCREMENT,
        #         page_id INTEGER NOT NULL,
        #         plus INTEGER NOT NULL,
        #         minus INTEGER NOT NULL,
        #         timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        #         FOREIGN KEY (page_id) REFERENCES pages (id)
        #     )
        #     """
        # )

        conn.commit()
    finally:
        conn.close()
