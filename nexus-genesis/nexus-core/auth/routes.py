"""
NEXUS Auth — API Routes
=========================

Endpoints:
    POST /auth/register  — Create new user account
    POST /auth/login     — Authenticate and get tokens
    POST /auth/refresh   — Refresh access token
    POST /auth/logout    — Revoke refresh token
    GET  /auth/me        — Get current user info

Security:
    - HTTP-only cookies for refresh token
    - Secure flag in production
    - CSRF protection placeholder
"""

import os
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from auth.service import (
    register_user,
    login_user,
    refresh_access_token,
    logout_user,
    get_current_user,
)
from auth.utils import verify_token
from auth.middleware import get_login_limiter

logger = logging.getLogger("nexus.auth.routes")

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Production detection
IS_PRODUCTION = os.getenv("NEXUS_ENV", "development") == "production"


# =============================================================================
# REQUEST MODELS
# =============================================================================

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    email: str
    password: str = Field(..., min_length=8)
    role: str = Field(default="viewer")


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str | None = None  # Can also come from cookie


# =============================================================================
# POST /auth/register
# =============================================================================

@router.post("/register")
async def register(req: RegisterRequest):
    """
    Register a new user account.
    
    Only admins can create operator/admin accounts.
    """
    result = register_user(
        username=req.username,
        email=req.email,
        password=req.password,
        role=req.role
    )
    
    if not result["success"]:
        return JSONResponse(
            status_code=400,
            content={"error": result["error"]}
        )
    
    return {
        "status": "registered",
        "user": result["user"]
    }


# =============================================================================
# POST /auth/login
# =============================================================================

@router.post("/login")
async def login(req: LoginRequest, request: Request, response: Response):
    """
    Authenticate user and return JWT tokens.
    
    Sets refresh token as HTTP-only cookie.
    Returns access token in response body.
    """
    # Rate limit check
    client_ip = request.client.host if request.client else "unknown"
    limiter = get_login_limiter()
    
    if not limiter.check(client_ip):
        logger.warning(f"Login rate limited: {client_ip}")
        return JSONResponse(
            status_code=429,
            content={"error": "Too many login attempts. Try again in 5 minutes."}
        )
    
    result = login_user(req.username, req.password)
    
    if not result["success"]:
        return JSONResponse(
            status_code=401,
            content={"error": result["error"]}
        )
    
    # Reset rate limiter on success
    limiter.reset(client_ip)
    
    # Set refresh token as HTTP-only cookie
    response.set_cookie(
        key="nexus_refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,  # 7 days
        path="/auth"
    )
    
    # Also set access token as HTTP-only cookie for middleware
    response.set_cookie(
        key="nexus_access_token",
        value=result["access_token"],
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
        max_age=15 * 60,  # 15 minutes
        path="/"
    )
    
    return {
        "status": "authenticated",
        "access_token": result["access_token"],
        "token_type": "bearer",
        "expires_in": 900,  # 15 minutes in seconds
        "user": result["user"]
    }


# =============================================================================
# POST /auth/refresh
# =============================================================================

@router.post("/refresh")
async def refresh(req: RefreshRequest, request: Request, response: Response):
    """
    Refresh access token using refresh token.
    
    Accepts refresh token from:
    1. Request body (refresh_token field)
    2. HTTP-only cookie (nexus_refresh_token)
    """
    # Get refresh token from body or cookie
    refresh_token = req.refresh_token or request.cookies.get("nexus_refresh_token")
    
    if not refresh_token:
        return JSONResponse(
            status_code=400,
            content={"error": "No refresh token provided"}
        )
    
    result = refresh_access_token(refresh_token)
    
    if not result["success"]:
        return JSONResponse(
            status_code=401,
            content={"error": result["error"]}
        )
    
    # Update access token cookie
    response.set_cookie(
        key="nexus_access_token",
        value=result["access_token"],
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
        max_age=15 * 60,
        path="/"
    )
    
    return {
        "status": "refreshed",
        "access_token": result["access_token"],
        "token_type": "bearer",
        "expires_in": 900
    }


# =============================================================================
# POST /auth/logout
# =============================================================================

@router.post("/logout")
async def logout(request: Request, response: Response):
    """
    Logout user by revoking refresh token and clearing cookies.
    """
    refresh_token = request.cookies.get("nexus_refresh_token")
    
    if refresh_token:
        logout_user(refresh_token)
    
    # Clear cookies
    response.delete_cookie("nexus_access_token", path="/")
    response.delete_cookie("nexus_refresh_token", path="/auth")
    
    return {"status": "logged_out"}


# =============================================================================
# GET /auth/me
# =============================================================================

@router.get("/me")
async def me(request: Request):
    """
    Get current authenticated user info.
    
    Requires valid access token.
    """
    # Try header first, then cookie
    token = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    else:
        token = request.cookies.get("nexus_access_token")
    
    if not token:
        return JSONResponse(
            status_code=401,
            content={"error": "Unauthorized"}
        )
    
    user = get_current_user(token)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Unauthorized", "detail": "Invalid or expired token"}
        )
    
    return {
        "status": "authenticated",
        "user": user
    }
