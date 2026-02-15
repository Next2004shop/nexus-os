"""
NEXUS Auth Package
====================

Production-grade JWT authentication layer.
"""

from auth.models import User, init_db
from auth.service import (
    register_user,
    login_user,
    refresh_access_token,
    logout_user,
    get_current_user,
    seed_admin,
)
from auth.routes import router as auth_router
from auth.middleware import AuthMiddleware

__all__ = [
    "User",
    "init_db",
    "register_user",
    "login_user",
    "refresh_access_token",
    "logout_user",
    "get_current_user",
    "seed_admin",
    "auth_router",
    "AuthMiddleware",
]
