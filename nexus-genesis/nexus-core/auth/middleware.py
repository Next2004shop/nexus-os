"""
NEXUS Auth — Middleware
========================

FastAPI middleware for JWT-based route protection.

Protects all routes matching protected prefixes.
Unauthorized requests return {"error": "Unauthorized"}.

Supports:
- Bearer token in Authorization header
- HTTP-only cookie (nexus_access_token)
- CSRF protection placeholder
- Login rate limiting
"""

import logging
import time
from collections import defaultdict
from typing import Set

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from auth.utils import verify_token, check_role

logger = logging.getLogger("nexus.auth.middleware")


# =============================================================================
# PROTECTED ROUTES
# =============================================================================

PROTECTED_PREFIXES: Set[str] = {
    "/execution",
    "/risk",
    "/command",
    "/intelligence",
    "/mt5",
    "/trade",
    "/kill",
    "/status",
}

# Public routes — always accessible
PUBLIC_ROUTES: Set[str] = {
    "/health",
    "/docs",
    "/openapi.json",
    "/auth/login",
    "/auth/register",
    "/auth/refresh",
}

# Routes requiring specific roles
ROLE_REQUIREMENTS = {
    "/execution": "operator",
    "/trade": "operator",
    "/kill": "admin",
    "/mt5": "operator",
    "/risk": "operator",
    "/command": "operator",
    "/intelligence": "viewer",
    "/status": "viewer",
}


# =============================================================================
# LOGIN RATE LIMITER
# =============================================================================

class LoginRateLimiter:
    """Rate limit login attempts per IP."""
    
    MAX_ATTEMPTS = 5
    WINDOW_SECONDS = 300  # 5 minutes
    
    def __init__(self):
        self._attempts: dict = defaultdict(list)
    
    def check(self, ip: str) -> bool:
        """Returns True if allowed, False if rate limited."""
        now = time.time()
        self._attempts[ip] = [
            t for t in self._attempts[ip]
            if now - t < self.WINDOW_SECONDS
        ]
        if len(self._attempts[ip]) >= self.MAX_ATTEMPTS:
            return False
        self._attempts[ip].append(now)
        return True
    
    def reset(self, ip: str):
        """Reset attempts for IP (on successful login)."""
        self._attempts.pop(ip, None)


_login_limiter = LoginRateLimiter()


def get_login_limiter() -> LoginRateLimiter:
    return _login_limiter


# =============================================================================
# AUTH MIDDLEWARE
# =============================================================================

class AuthMiddleware(BaseHTTPMiddleware):
    """
    JWT authentication middleware.
    
    Checks Authorization header (Bearer token) or HTTP-only cookie.
    Injects user info into request.state for downstream handlers.
    """
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method
        
        # Allow OPTIONS (CORS preflight)
        if method == "OPTIONS":
            return await call_next(request)
        
        # Allow public routes
        if self._is_public(path):
            return await call_next(request)
        
        # Check if route needs protection
        if not self._needs_protection(path):
            return await call_next(request)
        
        # Extract token
        token = self._extract_token(request)
        if not token:
            logger.warning(f"Unauthorized access attempt: {path}")
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized"}
            )
        
        # Verify token
        payload = verify_token(token, expected_type="access")
        if not payload:
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized", "detail": "Invalid or expired token"}
            )
        
        # Check role
        user_role = payload.get("role", "viewer")
        required_role = self._get_required_role(path)
        if required_role and not check_role(user_role, required_role):
            logger.warning(
                f"Insufficient role: {payload.get('username')} ({user_role}) "
                f"tried to access {path} (requires {required_role})"
            )
            return JSONResponse(
                status_code=403,
                content={"error": "Forbidden", "detail": f"Requires {required_role} role"}
            )
        
        # Inject user info into request state
        request.state.user_id = payload.get("sub")
        request.state.username = payload.get("username")
        request.state.user_role = user_role
        
        return await call_next(request)
    
    def _is_public(self, path: str) -> bool:
        """Check if route is public."""
        return path in PUBLIC_ROUTES or path.startswith("/auth/")
    
    def _needs_protection(self, path: str) -> bool:
        """Check if route matches protected prefixes."""
        return any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES)
    
    def _extract_token(self, request: Request) -> str | None:
        """Extract JWT from header or cookie."""
        # Try Authorization header first
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        
        # Try HTTP-only cookie
        return request.cookies.get("nexus_access_token")
    
    def _get_required_role(self, path: str) -> str | None:
        """Get required role for a path prefix."""
        for prefix, role in ROLE_REQUIREMENTS.items():
            if path.startswith(prefix):
                return role
        return None
