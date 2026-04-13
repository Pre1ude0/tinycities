from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import timedelta
from typing import Literal, cast

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Secrets:
    DB_PATH: str
    SECRET_KEY: str
    ALGORITHM: str
    EXPIRATION_DURATION: timedelta
    ACCESS_KEY_LENGTH: int
    KEYS_PATH: str
    COOKIE_SECURE: bool
    COOKIE_SAMESITE: Literal["lax", "strict", "none"]
    ADMIN_USERNAME: str | None
    ADMIN_TOKEN: str | None


DB_PATH: str = os.getenv("DB_PATH", "users.db")
KEYS_PATH: str = os.getenv("KEYS_PATH", "keys.txt")

SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRATION_DURATION: timedelta = timedelta(weeks=int(os.getenv("JWT_EXPIRE_WEEKS", "1")))

ACCESS_KEY_LENGTH: int = int(os.getenv("ACCESS_KEY_LENGTH", "24"))
ACCESS_KEYS_FILE: str = os.getenv("ACCESS_KEYS_FILE", "keys.txt")

COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() in ("1", "true", "yes", "on")

_cookie_samesite = os.getenv("COOKIE_SAMESITE", "lax").lower()
if _cookie_samesite not in ("lax", "strict", "none"):
    _cookie_samesite = "lax"
COOKIE_SAMESITE: Literal["lax", "strict", "none"] = cast(Literal["lax", "strict", "none"], _cookie_samesite)

ADMIN_USERNAME: str | None = os.getenv("ADMIN_USERNAME") or None
ADMIN_TOKEN: str | None = os.getenv("ADMIN_TOKEN") or None

secrets = Secrets(
    DB_PATH=DB_PATH,
    KEYS_PATH=KEYS_PATH,
    SECRET_KEY=SECRET_KEY,
    ALGORITHM=ALGORITHM,
    EXPIRATION_DURATION=EXPIRATION_DURATION,
    ACCESS_KEY_LENGTH=ACCESS_KEY_LENGTH,
    COOKIE_SECURE=COOKIE_SECURE,
    COOKIE_SAMESITE=COOKIE_SAMESITE,
    ADMIN_USERNAME=ADMIN_USERNAME,
    ADMIN_TOKEN=ADMIN_TOKEN,
)
