
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Optional
from core.secrets import secrets

@dataclass()
class PageRecord:
    id: int
    name: Optional[str]
    is_private: bool
    external_url: Optional[str]

def mkdir_page(name: str) -> None:
    import os
    page_dir = os.path.join(secrets.PAGE_SRV_PATH, name)
    os.makedirs(page_dir, exist_ok=True)

def enlist_page(conn: sqlite3.Connection, name: Optional[str], is_private: bool, external_url: Optional[str], owner_id: int) -> list[int]:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pages (name, is_private, external_url) VALUES (?, ?, ?)",
        (name, int(is_private), external_url),
    )
    if cur.rowcount == 0 or cur.lastrowid is None:
        raise Exception("Failed to create page")
    page_lastrowid = cur.lastrowid

    cur.execute(
        "INSERT INTO access (user_id, page_id, role) VALUES (?, ?, ?)",
        (owner_id, cur.lastrowid, 2)  # Owner gets admin role
    )
    if cur.rowcount == 0 or cur.lastrowid is None:
        raise Exception("Failed to assign page access to owner")
    access_lastrowid = cur.lastrowid

    return [int(page_lastrowid), int(access_lastrowid)]
