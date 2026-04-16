from __future__ import annotations

import os
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Cookie, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from core.security import get_payload
from core.secrets import secrets
from utils.users import parse_payload


router = APIRouter(prefix="/pages", tags=["files"])


def _utc_iso(ts: float) -> str:
	return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _ensure_dir(path: Path) -> None:
	path.mkdir(parents=True, exist_ok=True)


def _page_name_by_id(conn: sqlite3.Connection, page_id: int) -> Optional[str]:
	cur = conn.cursor()
	cur.execute("SELECT name FROM pages WHERE id = ?", (page_id,))
	row = cur.fetchone()
	if not row:
		return None
	return row[0]


def _role_for_user_page(conn: sqlite3.Connection, user_id: int, page_id: int) -> Optional[int]:
	cur = conn.cursor()
	cur.execute("SELECT role FROM access WHERE user_id = ? AND page_id = ?", (user_id, page_id))
	row = cur.fetchone()
	if not row:
		return None
	try:
		return int(row[0])
	except Exception:
		return None


def _require_user(access_token: str | None) -> dict[str, Any]:
	if access_token is None:
		raise HTTPException(status_code=401, detail="Unauthorized")
	payload = get_payload(access_token)
	user = parse_payload(payload)
	if user is None:
		raise HTTPException(status_code=401, detail="Unauthorized")
	return {"id": int(user.id), "username": str(user.username), "role": int(user.role)}


def _require_page_access(conn: sqlite3.Connection, user_id: int, page_id: int, min_role: int) -> int:
	role = _role_for_user_page(conn, user_id, page_id)
	if role is None:
		raise HTTPException(status_code=403, detail="Insufficient permissions")
	if int(role) < int(min_role):
		raise HTTPException(status_code=403, detail="Insufficient permissions")
	return int(role)


def _srv_root() -> Path:
	return Path(secrets.PAGE_SRV_PATH).resolve()


def _page_root_dir(page_name: str) -> Path:
	return (_srv_root() / page_name).resolve()


def _safe_join(root: Path, rel_path: str) -> Path:
	rel_path = rel_path or "/"
	rel_path = rel_path.replace("\\", "/")
	if "\x00" in rel_path:
		raise HTTPException(status_code=400, detail="Invalid path")

	candidate = (root / rel_path.lstrip("/")).resolve()
	try:
		if os.path.commonpath([str(root), str(candidate)]) != str(root):
			raise HTTPException(status_code=400, detail="Invalid path")
	except ValueError:
		raise HTTPException(status_code=400, detail="Invalid path")

	return candidate


def _node_info(root: Path, path: Path) -> dict[str, Any]:
	st = path.stat()
	rel = "/" + str(path.relative_to(root)).replace("\\", "/") if path != root else "/"
	if path.is_dir():
		return {
			"id": rel,
			"type": "folder",
			"name": path.name if path != root else "/",
			"size": 0,
			"date": _utc_iso(st.st_mtime),
		}
	return {
		"id": rel,
		"type": "file",
		"name": path.name,
		"size": int(st.st_size),
		"date": _utc_iso(st.st_mtime),
	}


class ListResponse(BaseModel):
	path: str
	items: list[dict[str, Any]]


class MkdirRequest(BaseModel):
	path: str = Field(..., description="Parent directory path, e.g. '/' or '/assets'")
	name: str = Field(..., min_length=1, max_length=255, description="Folder name")


class CreateFileRequest(BaseModel):
	path: str = Field(..., description="Parent directory path, e.g. '/' or '/assets'")
	name: str = Field(..., min_length=1, max_length=255, description="File name")


class RenameRequest(BaseModel):
	path: str = Field(..., description="Existing item path, e.g. '/assets/logo.png'")
	new_name: str = Field(..., min_length=1, max_length=255, description="New name (not a path)")


class DeleteRequest(BaseModel):
	paths: list[str] = Field(..., min_length=1, description="Paths to delete")


class MoveRequest(BaseModel):
	src: str = Field(..., description="Source path")
	dst_dir: str = Field(..., description="Destination directory path")


class CopyRequest(BaseModel):
	src: str = Field(..., description="Source path")
	dst_dir: str = Field(..., description="Destination directory path")


# Lists directory contents for Filemanager; validates auth/access and restricts traversal to the page's srv folder.
@router.get("/{page_id}/files", response_model=ListResponse)
def list_files(
	page_id: int,
	path: str = "/",
	access_token: str | None = Cookie(default=None),
):
	user = _require_user(access_token)

	conn = sqlite3.connect(secrets.DB_PATH)
	try:
		page_name = _page_name_by_id(conn, page_id)
		if not page_name:
			raise HTTPException(status_code=404, detail="Page not found")
		_require_page_access(conn, user["id"], page_id, min_role=1)
	finally:
		conn.close()

	root = _page_root_dir(page_name)
	_ensure_dir(root)

	target = _safe_join(root, path)
	if not target.exists():
		raise HTTPException(status_code=404, detail="Path not found")
	if not target.is_dir():
		raise HTTPException(status_code=400, detail="Path is not a directory")

	items: list[dict[str, Any]] = []
	for child in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
		items.append(_node_info(root, child))

	return {"path": path, "items": items}


# Creates a folder for Filemanager; checks access, validates name, and creates the directory.
@router.post("/{page_id}/files/folder")
def create_folder(
	page_id: int,
	req: MkdirRequest,
	access_token: str | None = Cookie(default=None),
):
	user = _require_user(access_token)

	conn = sqlite3.connect(secrets.DB_PATH)
	try:
		page_name = _page_name_by_id(conn, page_id)
		if not page_name:
			raise HTTPException(status_code=404, detail="Page not found")
		_require_page_access(conn, user["id"], page_id, min_role=1)
	finally:
		conn.close()

	root = _page_root_dir(page_name)
	_ensure_dir(root)

	parent = _safe_join(root, req.path)
	if not parent.exists() or not parent.is_dir():
		raise HTTPException(status_code=404, detail="Parent path not found")

	name = req.name.strip().replace("\\", "/")
	if "/" in name or name in (".", "..") or name == "":
		raise HTTPException(status_code=400, detail="Invalid folder name")

	new_dir = (parent / name).resolve()
	if os.path.commonpath([str(root), str(new_dir)]) != str(root):
		raise HTTPException(status_code=400, detail="Invalid folder name")

	if new_dir.exists():
		raise HTTPException(status_code=400, detail="Folder already exists")

	new_dir.mkdir(parents=False, exist_ok=False)
	return {"detail": "Folder created"}


# Creates an empty file for Filemanager; checks access, validates name, and creates the file.
@router.post("/{page_id}/files/empty")
def create_empty_file(
	page_id: int,
	req: CreateFileRequest,
	access_token: str | None = Cookie(default=None),
):
	user = _require_user(access_token)

	conn = sqlite3.connect(secrets.DB_PATH)
	try:
		page_name = _page_name_by_id(conn, page_id)
		if not page_name:
			raise HTTPException(status_code=404, detail="Page not found")
		_require_page_access(conn, user["id"], page_id, min_role=1)
	finally:
		conn.close()

	root = _page_root_dir(page_name)
	_ensure_dir(root)

	parent = _safe_join(root, req.path)
	if not parent.exists() or not parent.is_dir():
		raise HTTPException(status_code=404, detail="Parent path not found")

	name = req.name.strip().replace("\\", "/")
	if "/" in name or name in (".", "..") or name == "":
		raise HTTPException(status_code=400, detail="Invalid file name")

	new_file = (parent / name).resolve()
	if os.path.commonpath([str(root), str(new_file)]) != str(root):
		raise HTTPException(status_code=400, detail="Invalid file name")

	if new_file.exists():
		raise HTTPException(status_code=400, detail="File already exists")

	with open(new_file, "xb"):
		pass

	return {"detail": "File created"}


# Renames a file/folder for Filemanager; checks access, validates new name, and applies rename.
@router.post("/{page_id}/files/rename")
def rename_item(
	page_id: int,
	req: RenameRequest,
	access_token: str | None = Cookie(default=None),
):
	user = _require_user(access_token)

	conn = sqlite3.connect(secrets.DB_PATH)
	try:
		page_name = _page_name_by_id(conn, page_id)
		if not page_name:
			raise HTTPException(status_code=404, detail="Page not found")
		_require_page_access(conn, user["id"], page_id, min_role=1)
	finally:
		conn.close()

	root = _page_root_dir(page_name)
	_ensure_dir(root)

	src = _safe_join(root, req.path)
	if not src.exists():
		raise HTTPException(status_code=404, detail="Path not found")
	if src == root:
		raise HTTPException(status_code=400, detail="Cannot rename root")

	new_name = req.new_name.strip().replace("\\", "/")
	if "/" in new_name or new_name in (".", "..") or new_name == "":
		raise HTTPException(status_code=400, detail="Invalid new_name")

	dst = _safe_join(root, str(Path(req.path).parent).replace("\\", "/"))
	dst = (dst / new_name).resolve()
	if os.path.commonpath([str(root), str(dst)]) != str(root):
		raise HTTPException(status_code=400, detail="Invalid new_name")
	if dst.exists():
		raise HTTPException(status_code=400, detail="Destination already exists")

	src.rename(dst)
	return {"detail": "Renamed"}


# Deletes files/folders for Filemanager; checks access, validates paths, and removes items safely.
@router.post("/{page_id}/files/delete")
def delete_items(
	page_id: int,
	req: DeleteRequest,
	access_token: str | None = Cookie(default=None),
):
	user = _require_user(access_token)

	conn = sqlite3.connect(secrets.DB_PATH)
	try:
		page_name = _page_name_by_id(conn, page_id)
		if not page_name:
			raise HTTPException(status_code=404, detail="Page not found")
		_require_page_access(conn, user["id"], page_id, min_role=1)
	finally:
		conn.close()

	root = _page_root_dir(page_name)
	_ensure_dir(root)

	for p in req.paths:
		target = _safe_join(root, p)
		if not target.exists():
			continue
		if target == root:
			raise HTTPException(status_code=400, detail="Cannot delete root")
		if target.is_dir():
			shutil.rmtree(target)
		else:
			target.unlink(missing_ok=True)

	return {"detail": "Deleted"}


# Moves a file/folder for Filemanager; checks access, validates paths, and moves item.
@router.post("/{page_id}/files/move")
def move_item(
	page_id: int,
	req: MoveRequest,
	access_token: str | None = Cookie(default=None),
):
	user = _require_user(access_token)

	conn = sqlite3.connect(secrets.DB_PATH)
	try:
		page_name = _page_name_by_id(conn, page_id)
		if not page_name:
			raise HTTPException(status_code=404, detail="Page not found")
		_require_page_access(conn, user["id"], page_id, min_role=1)
	finally:
		conn.close()

	root = _page_root_dir(page_name)
	_ensure_dir(root)

	src = _safe_join(root, req.src)
	if not src.exists():
		raise HTTPException(status_code=404, detail="Source not found")

	dst_dir = _safe_join(root, req.dst_dir)
	if not dst_dir.exists() or not dst_dir.is_dir():
		raise HTTPException(status_code=404, detail="Destination directory not found")

	dst = (dst_dir / src.name).resolve()
	if os.path.commonpath([str(root), str(dst)]) != str(root):
		raise HTTPException(status_code=400, detail="Invalid destination")
	if dst.exists():
		raise HTTPException(status_code=400, detail="Destination already exists")

	shutil.move(str(src), str(dst))
	return {"detail": "Moved"}


# Copies a file/folder for Filemanager; checks access, validates paths, and copies item.
@router.post("/{page_id}/files/copy")
def copy_item(
	page_id: int,
	req: CopyRequest,
	access_token: str | None = Cookie(default=None),
):
	user = _require_user(access_token)

	conn = sqlite3.connect(secrets.DB_PATH)
	try:
		page_name = _page_name_by_id(conn, page_id)
		if not page_name:
			raise HTTPException(status_code=404, detail="Page not found")
		_require_page_access(conn, user["id"], page_id, min_role=1)
	finally:
		conn.close()

	root = _page_root_dir(page_name)
	_ensure_dir(root)

	src = _safe_join(root, req.src)
	if not src.exists():
		raise HTTPException(status_code=404, detail="Source not found")

	dst_dir = _safe_join(root, req.dst_dir)
	if not dst_dir.exists() or not dst_dir.is_dir():
		raise HTTPException(status_code=404, detail="Destination directory not found")

	dst = (dst_dir / src.name).resolve()
	if os.path.commonpath([str(root), str(dst)]) != str(root):
		raise HTTPException(status_code=400, detail="Invalid destination")
	if dst.exists():
		raise HTTPException(status_code=400, detail="Destination already exists")

	if src.is_dir():
		shutil.copytree(src, dst)
	else:
		shutil.copy2(src, dst)

	return {"detail": "Copied"}


# Uploads a file for Filemanager; checks access, validates target/filename, and writes to disk.
@router.post("/{page_id}/files/upload")
def upload_file(
	page_id: int,
	path: str = "/",
	file: UploadFile = File(...),
	access_token: str | None = Cookie(default=None),
):
	user = _require_user(access_token)

	conn = sqlite3.connect(secrets.DB_PATH)
	try:
		page_name = _page_name_by_id(conn, page_id)
		if not page_name:
			raise HTTPException(status_code=404, detail="Page not found")
		_require_page_access(conn, user["id"], page_id, min_role=1)
	finally:
		conn.close()

	root = _page_root_dir(page_name)
	_ensure_dir(root)

	target_dir = _safe_join(root, path)
	if not target_dir.exists() or not target_dir.is_dir():
		raise HTTPException(status_code=404, detail="Target directory not found")

	filename = (file.filename or "").strip().replace("\\", "/")
	if filename == "" or "/" in filename or filename in (".", ".."):
		raise HTTPException(status_code=400, detail="Invalid filename")

	dst = (target_dir / filename).resolve()
	if os.path.commonpath([str(root), str(dst)]) != str(root):
		raise HTTPException(status_code=400, detail="Invalid filename")

	with open(dst, "wb") as f:
		while True:
			chunk = file.file.read(1024 * 1024)
			if chunk == b"":
				break
			f.write(chunk)

	return {"detail": "Uploaded"}


# Downloads a file for Filemanager; checks access and streams the requested file.
@router.get("/{page_id}/files/download")
def download_file(
	page_id: int,
	path: str,
	access_token: str | None = Cookie(default=None),
):
	user = _require_user(access_token)

	conn = sqlite3.connect(secrets.DB_PATH)
	try:
		page_name = _page_name_by_id(conn, page_id)
		if not page_name:
			raise HTTPException(status_code=404, detail="Page not found")
		_require_page_access(conn, user["id"], page_id, min_role=1)
	finally:
		conn.close()

	root = _page_root_dir(page_name)
	_ensure_dir(root)

	target = _safe_join(root, path)
	if not target.exists() or not target.is_file():
		raise HTTPException(status_code=404, detail="File not found")

	return FileResponse(path=str(target), filename=target.name)
