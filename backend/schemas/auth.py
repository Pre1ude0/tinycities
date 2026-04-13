from __future__ import annotations

from pydantic import BaseModel, Field


USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 50
PASSWORD_MIN_LENGTH = 6


class LoginRequest(BaseModel):
    username: str = Field(...)
    password: str = Field(...)

class ModifyUserRequest(BaseModel):
    username: str | None = Field(None, min_length=USERNAME_MIN_LENGTH, max_length=USERNAME_MAX_LENGTH)
    password: str | None = Field(None, min_length=PASSWORD_MIN_LENGTH)

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=USERNAME_MIN_LENGTH, max_length=USERNAME_MAX_LENGTH)
    password: str = Field(..., min_length=PASSWORD_MIN_LENGTH)
    access_key: str = Field(...)
