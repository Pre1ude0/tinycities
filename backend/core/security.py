from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Literal, cast

import jwt
from fastapi import HTTPException, Response
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRATION_DURATION = timedelta(weeks=int(os.getenv("JWT_EXP_WEEKS", "1")))

COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() in ("1", "true", "yes", "on")
_cookie_samesite = os.getenv("COOKIE_SAMESITE", "lax").lower()
if _cookie_samesite not in ("lax", "strict", "none"):
    _cookie_samesite = "lax"
COOKIE_SAMESITE: Literal["lax", "strict", "none"] = cast(Literal["lax", "strict", "none"], _cookie_samesite)

COOKIE_NAME = os.getenv("AUTH_COOKIE_NAME", "access_token")
COOKIE_PATH = os.getenv("AUTH_COOKIE_PATH", "/")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(payload: dict) -> str:
    payload["exp"] = datetime.now(timezone.utc) + EXPIRATION_DURATION
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def set_access_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        COOKIE_NAME,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path=COOKIE_PATH,
        max_age=int(EXPIRATION_DURATION.total_seconds()),
    )


def clear_access_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path=COOKIE_PATH)


def get_payload(access_token: str | None) -> dict:
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("username")
    if not username or not isinstance(username, str):
        raise HTTPException(status_code=401, detail="Invalid token")

    return payload
