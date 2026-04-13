from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Cookie, HTTPException

from utils.users import parse_payload
from core.config import secrets
from core.security import get_payload
from utils.access_keys import generate_access_key, write_access_keys

router = APIRouter(tags=["keys"])


@router.get("/generate-key")
def generateAccessKey(n: int = 1, access_token: str | None = Cookie(default=None)):
    user = parse_payload(get_payload(access_token))
    amount = n if n is not None else 1

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if amount < 1:
        raise HTTPException(status_code=400, detail="amount must be >= 1")
    if amount > 100:
        raise HTTPException(status_code=400, detail="amount must be <= 1000")

    role = user.role
    if role is None:
        raise HTTPException(status_code=404, detail="User not found")
    if int(role) < 2:
        raise HTTPException(status_code=403, detail="Admins only")

    keys: list[str] = []

    for _ in range(amount):
        key = generate_access_key(secrets.ACCESS_KEY_LENGTH)
        keys.append(key)

    write_access_keys(keys, secrets.KEYS_PATH)
    return {"access_keys": keys}
