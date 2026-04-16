from .auth import router as auth_router
from .keys import router as keys_router
from .users import router as users_router
from .pages import router as pages_router
from .files import router as files_router

__all__ = ["auth_router", "keys_router", "users_router", "pages_router", "files_router"]
