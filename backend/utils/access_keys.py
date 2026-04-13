from __future__ import annotations

import os
import secrets
import string
from typing import Set


def access_keys_file_path() -> str:
    return os.getenv("KEYS_PATH", "keys.txt")


def access_key_length() -> int:
    try:
        return int(os.getenv("ACCESS_KEY_LENGTH", "24"))
    except ValueError:
        return 24


def load_access_keys(path: str | None = None) -> Set[str]:
    file_path = path or access_keys_file_path()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return {line.strip() for line in f if line.strip()}
    except FileNotFoundError:
        return set()


def write_access_keys(keys: Set[str], path: str | None = None) -> None:
    file_path = path or access_keys_file_path()
    with open(file_path, "w", encoding="utf-8") as f:
        for k in sorted(keys):
            f.write(k + "\n")


def generate_one_time_access_key(length: int | None = None) -> str:
    n = length if length is not None else access_key_length()
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))
