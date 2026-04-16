from __future__ import annotations

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from utils.errors import validation_exception_handler
from routes import auth_router, keys_router, users_router, pages_router, files_router
from db.sqlite import init_db
from db.srv import mkdir_srv

def create_app() -> FastAPI:
    app = FastAPI(root_path="/api")

    @app.exception_handler(RequestValidationError)
    async def _request_validation_handler(request, exc):
        return await validation_exception_handler(request, exc)

    @app.on_event("startup")
    def on_startup() -> None:
        init_db()
        mkdir_srv()

    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(keys_router)
    app.include_router(pages_router)
    app.include_router(files_router)

    return app


app = create_app()
