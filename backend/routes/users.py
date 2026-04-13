from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Cookie, HTTPException

from core.config import secrets
from core.security import get_payload
from utils.users import parse_payload

router = APIRouter(tags=["users"])


@router.get("/whoami")
def whoami(access_token: str | None = Cookie(default=None)):
    user = parse_payload(get_payload(access_token))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
