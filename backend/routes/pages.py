from __future__ import annotations

from fastapi import APIRouter, Cookie, HTTPException
from core.secrets import secrets
from schemas.pages import CreatePageRequest
from core.security import get_payload
from utils.users import parse_payload
from utils.pages import enlist_page, mkdir_page
import sqlite3

router = APIRouter(tags=["pages"])

import re

@router.post("/pages")
def create_page(
    page_request: CreatePageRequest,
    access_token: str | None = Cookie(default=None)
):
    if access_token is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user = parse_payload(get_payload(access_token))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role is None or int(user.role) < 1:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    if page_request.external_url is None and page_request.page_name is None:
        raise HTTPException(status_code=400, detail="Either page_name or external_url must be provided")
    elif page_request.external_url is not None and page_request.page_name is not None:
        raise HTTPException(status_code=400, detail="Only one of page_name or external_url can be provided")

    if page_request.page_name is not None and page_request.page_name != "":
        subdomain_pattern = re.compile(r'^(?=.{1,63}$)[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$')
        if not re.match(subdomain_pattern, page_request.page_name.lower()):
            raise HTTPException(status_code=400, detail="page_name is not a valid subdomain")
        else:
            page_request.page_name = page_request.page_name.lower()

    elif page_request.external_url is not None and page_request.external_url != "":
        url_pattern = re.compile(
            r'^(https?://)?'  # optional scheme
            r'(([A-Za-z0-9-]+\.)+[A-Za-z]{2,})'  # domain
            r'(:\d+)?'  # optional port
            r'(\/\S*)?$'  # optional path
        )
        if not re.match(url_pattern, page_request.external_url.lower()):
            raise HTTPException(status_code=400, detail="external_url is not a valid URL")
        else:
            page_request.external_url = page_request.external_url.lower()
    else:
        raise HTTPException(status_code=400, detail="page_name and external_url cannot be empty")

    conn = sqlite3.connect(secrets.DB_PATH)
    try:
        page_id, access_id = enlist_page(conn, page_request.page_name, page_request.is_private, page_request.external_url, user.id)
        conn.commit()
        if page_request.page_name is not None:
            mkdir_page(page_request.page_name)
        return {"detail": "Page created successfully", "page_id": page_id, "access_id": access_id}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Page name already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("/pages")
def list_pages(
    access_token: str | None = Cookie(default=None)
):
    if access_token is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user = parse_payload(get_payload(access_token))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    conn = sqlite3.connect(secrets.DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            """
                SELECT p.*, a.role
                FROM pages p
                LEFT JOIN access a
                    ON p.id = a.page_id AND a.user_id = ?
                WHERE p.is_private = 0
                    OR a.user_id IS NOT NULL;
            """,
            (user.id,)
        )
        pages = [
            {
                "id": row[0],
                "name": row[1],
                "is_private": bool(row[2]),
                "external_url": row[3],
                "role": row[4]
            }
            for row in cur.fetchall()
        ]
        return {"pages": pages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
