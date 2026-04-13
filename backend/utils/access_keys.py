from __future__ import annotations

import os
import secrets
import string
import time
import base64

def access_keys_file_path() -> str:
    return os.getenv("KEYS_PATH", "keys.txt")


def access_key_length() -> int:
    try:
        return int(os.getenv("ACCESS_KEY_LENGTH", "24"))
    except ValueError:
        return 24


def load_access_keys(path: str | None = None) -> list[str]:
    file_path = path or access_keys_file_path()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []


def write_access_keys(keys: list[str], path: str | None = None) -> None:
    file_path = path or access_keys_file_path()
    with open(file_path, "w", encoding="utf-8") as f:
        for k in sorted(keys):
            f.write(k + "\n")


def generate_access_key(length: int | None = None) -> str:
    n = length if length is not None else access_key_length()
    alphabet = string.ascii_letters + string.digits
    timestamp = str(int(time.time() * 1000))
    timestamp_b64 = base64.urlsafe_b64encode(timestamp.encode("utf-8")).decode("utf-8").rstrip("=")
    if n <= len(timestamp_b64):
        return timestamp_b64[-n:]
    random_part = "".join(secrets.choice(alphabet) for _ in range(n - len(timestamp_b64)))
    return random_part + timestamp_b64
