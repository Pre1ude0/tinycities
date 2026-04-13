from __future__ import annotations


from fastapi import APIRouter, Cookie, HTTPException

from schemas.auth import ModifyUserRequest
from core.config import secrets
from core.security import get_payload
from utils.users import parse_payload, update_user
from core.security import hash_password
import sqlite3

router = APIRouter(tags=["users"])


@router.get("/whoami")
def whoAmI(access_token: str | None = Cookie(default=None)):
    user = parse_payload(get_payload(access_token))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/usrmod")
def modifyUser(
    new_credentials: ModifyUserRequest,
    access_token: str | None = Cookie(default=None)
):
    user = parse_payload(get_payload(access_token))

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if new_credentials.username is None and new_credentials.password is None:
        raise HTTPException(status_code=400, detail="No fields to update")

    new_fields = {}

    if new_credentials.username is not None:
        new_fields["username"] = new_credentials.username

    if new_credentials.password is not None:
        new_fields["password"] = hash_password(new_credentials.password)

    conn = sqlite3.connect(secrets.DB_PATH)
    did_rows_change = update_user(conn, user.id, **new_fields)
    conn.commit()
    conn.close()

    return {"success": did_rows_change > 0}
