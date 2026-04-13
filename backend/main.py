from __future__ import annotations

import os
import secrets
import sqlite3
import string
from datetime import datetime, timedelta, timezone
from typing import Set, Literal, cast

import jwt
from dotenv import load_dotenv
from fastapi import Cookie, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from pydantic import BaseModel, Field

load_dotenv()

app = FastAPI(root_path="/api")

DB_PATH = os.getenv("DB_PATH", "users.db")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
EXPIRATION_DURATION = timedelta(weeks=1)

ACCESS_KEY_LENGTH = int(os.getenv("ACCESS_KEY_LENGTH", "24"))
ACCESS_KEYS_FILE = os.getenv("ACCESS_KEYS_FILE", "keys.txt")

COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() in ("1", "true", "yes", "on")
_cookie_samesite = os.getenv("COOKIE_SAMESITE", "lax").lower()
if _cookie_samesite not in ("lax", "strict", "none"):
	_cookie_samesite = "lax"
COOKIE_SAMESITE: Literal["lax", "strict", "none"] = cast(Literal["lax", "strict", "none"], _cookie_samesite)


class LoginRequest(BaseModel):
	username: str = Field(...)
	password: str = Field(...)


class RegisterRequest(BaseModel):
	username: str = Field(..., min_length=3, max_length=50)
	password: str = Field(..., min_length=6)
	access_key: str = Field(...)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
	errors = exc.errors()
	first_error = errors[0]
	field = first_error["loc"][-1]
	message = first_error["msg"]
	return JSONResponse(status_code=422, content={"detail": f"{field}: {message}"})


def init_db() -> None:
	conn = sqlite3.connect(DB_PATH)
	try:
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS users (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				username TEXT NOT NULL UNIQUE,
				password TEXT NOT NULL,
				role INT NOT NULL DEFAULT 1
			)
			"""
		)

		admin_username = os.getenv("ADMIN_USERNAME")
		admin_token = os.getenv("ADMIN_TOKEN")
		if admin_username and admin_token:
			hashed_admin_password = pwd_context.hash(admin_token)
			conn.execute(
				"""
				INSERT OR IGNORE INTO users (username, password, role)
				VALUES (?, ?, 2)
				""",
				(admin_username, hashed_admin_password),
			)

		conn.commit()
	finally:
		conn.close()


@app.on_event("startup")
def on_startup() -> None:
	init_db()


def create_access_token(username: str) -> str:
	payload = {
		"username": username,
		"exp": datetime.now(timezone.utc) + EXPIRATION_DURATION,
	}
	return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def set_access_cookie(response: Response, token: str) -> None:
	response.set_cookie(
		"access_token",
		value=token,
		httponly=True,
		secure=COOKIE_SECURE,
		samesite=COOKIE_SAMESITE,
		path="/",
		max_age=int(EXPIRATION_DURATION.total_seconds()),
	)


def clear_access_cookie(response: Response) -> None:
	response.delete_cookie("access_token", path="/")


def get_current_username(access_token: str | None) -> str:
	if not access_token:
		raise HTTPException(status_code=401, detail="Not authenticated")
	try:
		payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
		username = payload.get("username")
		if not username:
			raise HTTPException(status_code=401, detail="Invalid token")
		return username
	except jwt.PyJWTError:
		raise HTTPException(status_code=401, detail="Invalid token")


def load_access_keys() -> Set[str]:
	try:
		with open(ACCESS_KEYS_FILE, "r", encoding="utf-8") as f:
			return {line.strip() for line in f if line.strip()}
	except FileNotFoundError:
		return set()


def write_access_keys(keys: Set[str]) -> None:
	with open(ACCESS_KEYS_FILE, "w", encoding="utf-8") as f:
		for k in sorted(keys):
			f.write(k + "\n")


def generate_one_time_access_key() -> str:
	alphabet = string.ascii_letters + string.digits
	return "".join(secrets.choice(alphabet) for _ in range(ACCESS_KEY_LENGTH))


@app.post("/login")
def login(login_request: LoginRequest, response: Response):
	conn = sqlite3.connect(DB_PATH)
	try:
		cursor = conn.cursor()
		cursor.execute("SELECT password FROM users WHERE username=?", (login_request.username,))
		row = cursor.fetchone()

		if not row or not pwd_context.verify(login_request.password, row[0]):
			raise HTTPException(status_code=401, detail="Invalid credentials")

		token = create_access_token(login_request.username)
		clear_access_cookie(response)
		set_access_cookie(response, token)
		return {"detail": "Login successful"}
	finally:
		conn.close()


@app.post("/register")
def register_user(req: RegisterRequest, response: Response):
	keys = load_access_keys()
	if not keys:
		raise HTTPException(status_code=400, detail="No access keys available")
	if req.access_key not in keys:
		raise HTTPException(status_code=403, detail="Invalid access key")

	conn = sqlite3.connect(DB_PATH)
	try:
		cursor = conn.cursor()

		cursor.execute("SELECT 1 FROM users WHERE username=?", (req.username,))
		if cursor.fetchone():
			raise HTTPException(status_code=400, detail="Username already exists")

		hashed_password = pwd_context.hash(req.password)
		cursor.execute(
			"""
			INSERT INTO users (username, password, role)
			VALUES (?, ?, 1)
			""",
			(req.username, hashed_password),
		)
		conn.commit()
	finally:
		conn.close()

	keys.discard(req.access_key)
	write_access_keys(keys)

	token = create_access_token(req.username)
	clear_access_cookie(response)
	set_access_cookie(response, token)
	return {"detail": "User registered successfully"}


@app.post("/logout")
def logout(response: Response):
	clear_access_cookie(response)
	return {"detail": "Logged out"}


@app.get("/whoami")
def whoami(access_token: str | None = Cookie(default=None)):
	username = get_current_username(access_token)

	conn = sqlite3.connect(DB_PATH)
	try:
		cursor = conn.cursor()
		cursor.execute("SELECT id, username, role FROM users WHERE username=?", (username,))
		user = cursor.fetchone()
		if not user:
			raise HTTPException(status_code=404, detail="User not found")
		return {"id": user[0], "username": user[1], "role": int(user[2])}
	finally:
		conn.close()


@app.get("/generate-key")
def generate_access_key(amount: int = 1, access_token: str | None = Cookie(default=None)):
	username = get_current_username(access_token)

	if amount < 1:
		raise HTTPException(status_code=400, detail="amount must be >= 1")
	if amount > 1000:
		raise HTTPException(status_code=400, detail="amount must be <= 1000")

	conn = sqlite3.connect(DB_PATH)
	try:
		cursor = conn.cursor()
		cursor.execute("SELECT role FROM users WHERE username=?", (username,))
		row = cursor.fetchone()

		if not row:
			raise HTTPException(status_code=404, detail="User not found")
		if int(row[0]) < 2:
			raise HTTPException(status_code=403, detail="Admins only")

		keys = load_access_keys()
		generated_keys: list[str] = []

		for _ in range(amount):
			access_key = generate_one_time_access_key()
			while access_key in keys:
				access_key = generate_one_time_access_key()
			keys.add(access_key)
			generated_keys.append(access_key)

		write_access_keys(keys)
		return {"access_keys": generated_keys}
	finally:
		conn.close()
