"""
NEXUS Auth — Utilities
========================

JWT token creation/verification and password hashing.

Tokens:
- Access token: 15 min expiry, contains user_id + role
- Refresh token: 7 days expiry, stored as hash in SQLite

Passwords:
- bcrypt hashing with auto-salt
"""

import os
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

import jwt
import bcrypt

logger = logging.getLogger("nexus.auth.utils")

# =============================================================================
# JWT CONFIGURATION
# =============================================================================

# Secret key — MUST be set in production via ENV
JWT_SECRET = os.getenv("JWT_SECRET", "nexus-dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Valid roles
VALID_ROLES = {"admin", "operator", "viewer"}
ROLE_HIERARCHY = {"admin": 3, "operator": 2, "viewer": 1}


# =============================================================================
# PASSWORD HASHING
# =============================================================================

def hash_password(password: str) -> str:
    """Hash password with bcrypt + auto-salt."""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8")
        )
    except Exception:
        return False


# =============================================================================
# JWT TOKEN OPERATIONS
# =============================================================================

def create_access_token(user_id: str, username: str, role: str) -> str:
    """
    Create a short-lived access token (15 min).
    
    Payload:
        sub: user_id
        username: str
        role: str
        type: "access"
        exp: datetime
        iat: datetime
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """
    Create a long-lived refresh token (7 days).
    
    Payload:
        sub: user_id
        type: "refresh"
        exp: datetime
        iat: datetime
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str, expected_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.
    
    Returns payload dict if valid, None if invalid/expired.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        if payload.get("type") != expected_type:
            logger.warning(f"Token type mismatch: expected {expected_type}, got {payload.get('type')}")
            return None
        
        return payload
    
    except jwt.ExpiredSignatureError:
        logger.debug("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


def hash_token(token: str) -> str:
    """Hash a token for storage (refresh tokens stored as hashes)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def get_refresh_token_expiry() -> str:
    """Get refresh token expiry as ISO string."""
    return (datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)).isoformat()


# =============================================================================
# ROLE VALIDATION
# =============================================================================

def check_role(user_role: str, required_role: str) -> bool:
    """Check if user's role meets or exceeds required role."""
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    required_level = ROLE_HIERARCHY.get(required_role, 999)
    return user_level >= required_level


def validate_password_strength(password: str) -> tuple:
    """
    Validate password strength.
    
    Returns (valid: bool, errors: list[str])
    """
    errors = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters")
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")
    
    return len(errors) == 0, errors
