from __future__ import annotations

import argparse
import getpass
import sqlite3
import sys
from typing import Optional


def _connect(db_path: str) -> sqlite3.Connection:
	conn = sqlite3.connect(db_path)
	conn.row_factory = sqlite3.Row
	return conn


def _get_user(conn: sqlite3.Connection, username: str) -> Optional[sqlite3.Row]:
	cur = conn.execute(
		"SELECT id, username, role FROM users WHERE username = ?",
		(username,),
	)
	return cur.fetchone()


def cmd_show_user(db_path: str, username: str) -> int:
	conn = _connect(db_path)
	try:
		row = _get_user(conn, username)
		if not row:
			print("User not found")
			return 1
		print(f"id={row['id']} username={row['username']} role={row['role']}")
		return 0
	finally:
		conn.close()


def cmd_list_users(db_path: str) -> int:
	conn = _connect(db_path)
	try:
		cur = conn.execute("SELECT id, username, role FROM users ORDER BY id ASC")
		rows = cur.fetchall()
		for r in rows:
			print(f"{r['id']}\t{r['username']}\trole={r['role']}")
		return 0
	finally:
		conn.close()


def cmd_set_role(db_path: str, username: str, role: int) -> int:
	if role < 0:
		print("role must be >= 0", file=sys.stderr)
		return 2

	conn = _connect(db_path)
	try:
		row = _get_user(conn, username)
		if not row:
			print("User not found", file=sys.stderr)
			return 1

		conn.execute(
			"UPDATE users SET role = ? WHERE username = ?",
			(int(role), username),
		)
		conn.commit()
		print(f"Updated role for {username} to {role}")
		return 0
	finally:
		conn.close()


def _prompt_new_password(confirm: bool) -> str:
	p1 = getpass.getpass("New password: ")
	if confirm:
		p2 = getpass.getpass("Confirm password: ")
		if p1 != p2:
			raise ValueError("Passwords do not match")
	if not p1:
		raise ValueError("Password cannot be empty")
	return p1


def cmd_reset_password(db_path: str, username: str, password: Optional[str], confirm: bool) -> int:
	try:
		from core.security import hash_password
	except Exception as e:
		print(f"Failed to import password hashing from core.security: {e}", file=sys.stderr)
		return 2

	conn = _connect(db_path)
	try:
		row = _get_user(conn, username)
		if not row:
			print("User not found", file=sys.stderr)
			return 1

		if password is None:
			password = _prompt_new_password(confirm=confirm)

		pw_hash = hash_password(password)
		conn.execute(
			"UPDATE users SET password = ? WHERE username = ?",
			(pw_hash, username),
		)
		conn.commit()
		print(f"Password reset for {username}")
		return 0
	except ValueError as ve:
		print(str(ve), file=sys.stderr)
		return 2
	finally:
		conn.close()


def cmd_create_user(db_path: str, username: str, password: Optional[str], role: int, confirm: bool) -> int:
	try:
		from core.security import hash_password
	except Exception as e:
		print(f"Failed to import password hashing from core.security: {e}", file=sys.stderr)
		return 2

	if not username:
		print("username is required", file=sys.stderr)
		return 2

	if password is None:
		try:
			password = _prompt_new_password(confirm=confirm)
		except ValueError as ve:
			print(str(ve), file=sys.stderr)
			return 2

	conn = _connect(db_path)
	try:
		if _get_user(conn, username):
			print("User already exists", file=sys.stderr)
			return 1

		pw_hash = hash_password(password)
		conn.execute(
			"INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
			(username, pw_hash, int(role)),
		)
		conn.commit()
		print(f"Created user {username} with role={role}")
		return 0
	finally:
		conn.close()


def build_parser() -> argparse.ArgumentParser:
	p = argparse.ArgumentParser(prog="kit", description="Local admin kit for tinycities backend")
	p.add_argument(
		"--db",
		default=None,
		help="Path to sqlite DB. If omitted, uses core.secrets.secrets.DB_PATH",
	)

	sub = p.add_subparsers(dest="cmd", required=True)

	sp = sub.add_parser("show-user", help="Show a user by username")
	sp.add_argument("username")

	lp = sub.add_parser("list-users", help="List all users")

	rp = sub.add_parser("reset-password", help="Reset a user's password (writes bcrypt hash)")
	rp.add_argument("username")
	rp.add_argument("--password", default=None, help="New password (unsafe in shell history). Omit to prompt.")
	rp.add_argument("--confirm", action="store_true", help="Ask to confirm password when prompting")

	sr = sub.add_parser("set-role", help="Set a user's role (0=no access, 1=user, 2=admin)")
	sr.add_argument("username")
	sr.add_argument("role", type=int)

	cu = sub.add_parser("create-user", help="Create a new user locally")
	cu.add_argument("username")
	cu.add_argument("--password", default=None, help="Password (unsafe in shell history). Omit to prompt.")
	cu.add_argument("--role", type=int, default=1)
	cu.add_argument("--confirm", action="store_true", help="Ask to confirm password when prompting")

	return p


def resolve_db_path(cli_db: Optional[str]) -> str:
	if cli_db:
		return cli_db
	try:
		from core.secrets import secrets

		return secrets.DB_PATH
	except Exception:
		return "users.db"


def main(argv: list[str]) -> int:
	parser = build_parser()
	args = parser.parse_args(argv)

	db_path = resolve_db_path(args.db)

	if args.cmd == "show-user":
		return cmd_show_user(db_path, args.username)
	if args.cmd == "list-users":
		return cmd_list_users(db_path)
	if args.cmd == "reset-password":
		return cmd_reset_password(db_path, args.username, args.password, args.confirm)
	if args.cmd == "set-role":
		return cmd_set_role(db_path, args.username, args.role)
	if args.cmd == "create-user":
		return cmd_create_user(db_path, args.username, args.password, args.role, args.confirm)

	print("Unknown command", file=sys.stderr)
	return 2


if __name__ == "__main__":
	raise SystemExit(main(sys.argv[1:]))
