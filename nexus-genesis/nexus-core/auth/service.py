"""
NEXUS Auth — Service Layer
============================

Core authentication business logic:
- Register user
- Login (returns access + refresh tokens)
- Refresh access token
- Logout (revoke refresh token)
- Get current user
- Seed admin on first startup
"""

import os
import logging
from typing import Optional, Dict, Any, Tuple

from auth.models import (
    User,
    create_user,
    get_user_by_username,
    get_user_by_email,
    get_user_by_id,
    update_last_login,
    get_user_count,
    store_refresh_token,
    get_refresh_token,
    revoke_refresh_token,
    revoke_all_user_tokens,
)
from auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    hash_token,
    get_refresh_token_expiry,
    validate_password_strength,
    VALID_ROLES,
)

logger = logging.getLogger("nexus.auth.service")


# =============================================================================
# REGISTRATION
# =============================================================================

def register_user(
    username: str,
    email: str,
    password: str,
    role: str = "viewer"
) -> Dict[str, Any]:
    """
    Register a new user.
    
    Returns:
        {"success": bool, "user": dict | None, "error": str | None}
    """
    # Validate inputs
    if not username or len(username) < 3:
        return {"success": False, "user": None, "error": "Username must be at least 3 characters"}
    
    if not email or "@" not in email:
        return {"success": False, "user": None, "error": "Invalid email address"}
    
    if role not in VALID_ROLES:
        return {"success": False, "user": None, "error": f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}"}
    
    # Validate password strength
    strong, errors = validate_password_strength(password)
    if not strong:
        return {"success": False, "user": None, "error": "; ".join(errors)}
    
    # Check if username/email already exists
    if get_user_by_username(username):
        return {"success": False, "user": None, "error": "Username already taken"}
    
    if get_user_by_email(email):
        return {"success": False, "user": None, "error": "Email already registered"}
    
    # Create user with hashed password
    try:
        pw_hash = hash_password(password)
        user = create_user(username, email, pw_hash, role)
        logger.info(f"User registered: {username} (role={role})")
        return {"success": True, "user": user.to_dict(), "error": None}
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        return {"success": False, "user": None, "error": str(e)}


# =============================================================================
# LOGIN
# =============================================================================

def login_user(username: str, password: str) -> Dict[str, Any]:
    """
    Authenticate user and return tokens.
    
    Returns:
        {
            "success": bool,
            "access_token": str | None,
            "refresh_token": str | None,
            "user": dict | None,
            "error": str | None
        }
    """
    # Find user
    user = get_user_by_username(username)
    if not user:
        # Also try email
        user = get_user_by_email(username)
    
    if not user:
        logger.warning(f"Login failed: user '{username}' not found")
        return {
            "success": False,
            "access_token": None,
            "refresh_token": None,
            "user": None,
            "error": "Invalid credentials"
        }
    
    # Verify password
    if not verify_password(password, user.password_hash):
        logger.warning(f"Login failed: wrong password for '{username}'")
        return {
            "success": False,
            "access_token": None,
            "refresh_token": None,
            "user": None,
            "error": "Invalid credentials"
        }
    
    # Generate tokens
    access_token = create_access_token(user.id, user.username, user.role)
    refresh_token = create_refresh_token(user.id)
    
    # Store refresh token hash
    store_refresh_token(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=get_refresh_token_expiry()
    )
    
    # Update last login
    update_last_login(user.id)
    
    logger.info(f"Login successful: {user.username} (role={user.role})")
    
    return {
        "success": True,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict(),
        "error": None
    }


# =============================================================================
# TOKEN REFRESH
# =============================================================================

def refresh_access_token(refresh_token_str: str) -> Dict[str, Any]:
    """
    Use refresh token to get new access token.
    
    Returns:
        {"success": bool, "access_token": str | None, "error": str | None}
    """
    # Verify refresh token
    payload = verify_token(refresh_token_str, expected_type="refresh")
    if not payload:
        return {"success": False, "access_token": None, "error": "Invalid or expired refresh token"}
    
    # Check if token is stored and not revoked
    token_hash = hash_token(refresh_token_str)
    stored = get_refresh_token(token_hash)
    if not stored:
        logger.warning("Refresh token not found or revoked")
        return {"success": False, "access_token": None, "error": "Refresh token revoked"}
    
    # Get user
    user_id = payload.get("sub")
    user = get_user_by_id(user_id)
    if not user:
        return {"success": False, "access_token": None, "error": "User not found"}
    
    # Issue new access token
    new_access = create_access_token(user.id, user.username, user.role)
    
    logger.info(f"Access token refreshed for: {user.username}")
    return {"success": True, "access_token": new_access, "error": None}


# =============================================================================
# LOGOUT
# =============================================================================

def logout_user(refresh_token_str: str) -> Dict[str, Any]:
    """
    Logout by revoking refresh token.
    
    Returns:
        {"success": bool, "error": str | None}
    """
    token_hash = hash_token(refresh_token_str)
    revoke_refresh_token(token_hash)
    logger.info("User logged out, refresh token revoked")
    return {"success": True, "error": None}


def logout_all(user_id: str) -> Dict[str, Any]:
    """Revoke all refresh tokens for a user."""
    revoke_all_user_tokens(user_id)
    logger.info(f"All sessions revoked for user: {user_id[:8]}...")
    return {"success": True, "error": None}


# =============================================================================
# GET CURRENT USER
# =============================================================================

def get_current_user(token: str) -> Optional[Dict[str, Any]]:
    """
    Get current user from access token.
    
    Returns user dict or None.
    """
    payload = verify_token(token, expected_type="access")
    if not payload:
        return None
    
    user = get_user_by_id(payload.get("sub"))
    if not user:
        return None
    
    return user.to_dict()


# =============================================================================
# ADMIN SEED
# =============================================================================

def seed_admin():
    """
    On first startup: create admin user from ENV variables.
    
    ENV:
        ADMIN_USER — admin username
        ADMIN_PASS — admin password
    
    Only runs if zero users exist in the database.
    """
    if get_user_count() > 0:
        logger.info("Users exist, skipping admin seed")
        return
    
    admin_user = os.getenv("ADMIN_USER", "admin")
    admin_pass = os.getenv("ADMIN_PASS")
    
    if not admin_pass:
        # Generate a default password and print it
        import secrets
        admin_pass = secrets.token_urlsafe(16)
        print("\n" + "=" * 60)
        print("🔐  NEXUS ADMIN SEED — First Run")
        print(f"   Username: {admin_user}")
        print(f"   Password: {admin_pass}")
        print("   ⚠  SAVE THIS PASSWORD — it will not be shown again!")
        print("   Set ADMIN_USER and ADMIN_PASS in .env to customize.")
        print("=" * 60 + "\n")
    
    result = register_user(
        username=admin_user,
        email=f"{admin_user}@nexus.local",
        password=admin_pass,
        role="admin"
    )
    
    if result["success"]:
        logger.info(f"Admin user seeded: {admin_user}")
    else:
        logger.error(f"Admin seed failed: {result['error']}")
