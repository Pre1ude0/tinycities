from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional, Tuple

from fastapi import HTTPException

from core.secrets import secrets


AccessLevel = Literal["none", "viewer", "contributor", "admin"]


@dataclass(frozen=True)
class PageAccess:
	user_id: int
	page_id: int
	role: int

	@property
	def level(self) -> AccessLevel:
		if self.role >= 2:
			return "admin"
		if self.role == 1:
			return "contributor"
		if self.role == 0:
			return "viewer"
		return "none"


def get_page_name_by_id(conn: sqlite3.Connection, page_id: int) -> Optional[str]:
	cur = conn.cursor()
	cur.execute("SELECT name FROM pages WHERE id = ?", (int(page_id),))
	row = cur.fetchone()
	if not row:
		return None
	name = row[0]
	if name is None:
		return None
	return str(name)


def get_user_access_for_page(conn: sqlite3.Connection, user_id: int, page_id: int) -> Optional[PageAccess]:
	cur = conn.cursor()
	cur.execute(
		"SELECT user_id, page_id, role FROM access WHERE user_id = ? AND page_id = ?",
		(int(user_id), int(page_id)),
	)
	row = cur.fetchone()
	if not row:
		return None
	return PageAccess(user_id=int(row[0]), page_id=int(row[1]), role=int(row[2]))


def require_page_access(
	conn: sqlite3.Connection,
	user_id: int,
	page_id: int,
	min_role: int = 1,
) -> PageAccess:
	access = get_user_access_for_page(conn, user_id, page_id)
	if access is None:
		raise HTTPException(status_code=403, detail="Insufficient permissions")
	if int(access.role) < int(min_role):
		raise HTTPException(status_code=403, detail="Insufficient permissions")
	return access


def _base_srv_path() -> Path:
	return Path(secrets.PAGE_SRV_PATH).resolve()


def _is_safe_leaf_folder_name(name: str) -> bool:
	if not name:
		return False
	if name in (".", ".."):
		return False
	if "/" in name or "\\" in name:
		return False
	if "\x00" in name:
		return False
	return True


def resolve_page_srv_dir(conn: sqlite3.Connection, page_id: int) -> Path:
	"""
	Resolves the page's srv directory as:
	  <PAGE_SRV_PATH>/<page.name>/

	Validates:
	- page exists
	- page.name exists (not an external_url-only page)
	- folder name is a safe single path segment
	- result stays within PAGE_SRV_PATH
	"""
	name = get_page_name_by_id(conn, page_id)
	if name is None:
		raise HTTPException(status_code=404, detail="Page not found")

	if not _is_safe_leaf_folder_name(name):
		raise HTTPException(status_code=400, detail="Invalid page folder name")

	base = _base_srv_path()
	target = (base / name).resolve()

	try:
		target.relative_to(base)
	except ValueError:
		raise HTTPException(status_code=400, detail="Invalid path")

	return target


def ensure_page_srv_dir_exists(conn: sqlite3.Connection, page_id: int) -> Path:
	path = resolve_page_srv_dir(conn, page_id)
	path.mkdir(parents=True, exist_ok=True)
	return path


def resolve_path_within_page(
	conn: sqlite3.Connection,
	page_id: int,
	relative_path: str,
	allow_root: bool = True,
) -> Path:
	"""
	Resolves a user-provided relative path inside the page srv dir, preventing traversal.

	- relative_path may be "", ".", or "/" to indicate root (if allow_root=True)
	- rejects absolute paths and traversal
	"""
	page_dir = resolve_page_srv_dir(conn, page_id)

	p = (relative_path or "").strip()
	if p in ("", ".", "/"):
		if not allow_root:
			raise HTTPException(status_code=400, detail="Invalid path")
		return page_dir

	if p.startswith("/") or p.startswith("\\"):
		raise HTTPException(status_code=400, detail="Invalid path")

	joined = (page_dir / p).resolve()

	try:
		joined.relative_to(page_dir)
	except ValueError:
		raise HTTPException(status_code=400, detail="Invalid path")

	return joined


def require_int_page_id(page_id: str | int) -> int:
	try:
		pid = int(page_id)
	except (ValueError, TypeError):
		raise HTTPException(status_code=400, detail="Invalid page id")
	if pid < 1:
		raise HTTPException(status_code=400, detail="Invalid page id")
	return pid


def normalize_amount(amount: int, min_value: int = 1, max_value: int = 1000) -> int:
	try:
		a = int(amount)
	except (ValueError, TypeError):
		raise HTTPException(status_code=400, detail="Invalid amount")
	if a < min_value:
		raise HTTPException(status_code=400, detail=f"amount must be >= {min_value}")
	if a > max_value:
		raise HTTPException(status_code=400, detail=f"amount must be <= {max_value}")
	return a
