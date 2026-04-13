
from __future__ import annotations

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    first_error = errors[0] if errors else {"loc": ["body"], "msg": "Invalid request"}
    field = first_error["loc"][-1] if first_error.get("loc") else "body"
    message = first_error.get("msg", "Invalid request")

    return JSONResponse(status_code=422, content={"detail": f"{field}: {message}"})
