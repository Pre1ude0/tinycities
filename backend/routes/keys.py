from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Cookie, HTTPException

from utils.users import parse_payload
from core.config import secrets
from core.security import get_payload
from utils.access_keys import generate_one_time_access_key, load_access_keys, write_access_keys

router = APIRouter(tags=["keys"])


@router.get("/generate-key")
def generate_access_key(amount: int = 1, access_token: str | None = Cookie(default=None)):
    user = parse_payload(get_payload(access_token))

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if amount < 1:
        raise HTTPException(status_code=400, detail="amount must be >= 1")
    if amount > 1000:
        raise HTTPException(status_code=400, detail="amount must be <= 1000")

    conn = sqlite3.connect(secrets.DB_PATH)
    try:
        role = user.role
        if role is None:
            raise HTTPException(status_code=404, detail="User not found")
        if int(role) < 2:
            raise HTTPException(status_code=403, detail="Admins only")

        keys = load_access_keys(secrets.ACCESS_KEYS_FILE)
        generated_keys: list[str] = []

        for _ in range(amount):
            access_key = generate_one_time_access_key(secrets.ACCESS_KEY_LENGTH)
            while access_key in keys:
                access_key = generate_one_time_access_key(secrets.ACCESS_KEY_LENGTH)
            keys.add(access_key)
            generated_keys.append(access_key)

        write_access_keys(keys, secrets.ACCESS_KEYS_FILE)
        return {"access_keys": generated_keys}
    finally:
        conn.close()
