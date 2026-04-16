from __future__ import annotations

from pydantic import BaseModel, Field


class CreatePageRequest(BaseModel):
    page_name: str | None = Field(..., min_length=1, max_length=100)
    is_private: bool = Field(default=False)
    external_url: str | None = Field(default=None, max_length=200)
