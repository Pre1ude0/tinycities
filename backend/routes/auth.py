from __future__ import annotations

import sqlite3

from fastapi import APIRouter, HTTPException, Response

from core.config import secrets
from core.security import (
	clear_access_cookie,
	create_access_token,
	hash_password,
	set_access_cookie,
	verify_password,
)
from schemas.auth import LoginRequest, RegisterRequest
from utils.access_keys import write_access_keys, load_access_keys
from utils.users import create_user, username_exists

router = APIRouter(tags=["auth"])


@router.post("/login")
def login(login_request: LoginRequest, response: Response):
    conn = sqlite3.connect(secrets.DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("SELECT password, role, id FROM users WHERE username = ?", (login_request.username,))
        row = cur.fetchone()

        if not row or not verify_password(login_request.password, row[0]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        payload = {"username": login_request.username, "role": row[1], "id": row[2]}
        token = create_access_token(payload)
        set_access_cookie(response, token)
        return {"detail": "Login successful"}
    finally:
        conn.close()


@router.post("/register")
def register(req: RegisterRequest, response: Response):
    keys = load_access_keys(secrets.KEYS_PATH)


    if req.access_key not in keys:
        raise HTTPException(status_code=403, detail="Invalid access key")

    conn = sqlite3.connect(secrets.DB_PATH)
    try:
        if username_exists(conn, req.username):
            raise HTTPException(status_code=400, detail="Username already exists")

        password_hash = hash_password(req.password)
        id = create_user(conn, req.username, password_hash, role=1)
        conn.commit()
    finally:
        conn.close()

    keys.remove(req.access_key)
    write_access_keys(keys, secrets.KEYS_PATH)

    payload = {"username": req.username, "role": 1, "id": id}
    token = create_access_token(payload)
    clear_access_cookie(response)
    set_access_cookie(response, token)
    return {"detail": "User registered successfully"}
