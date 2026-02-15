"""
NEXUS Auth — User Model + SQLite Store
========================================

Lightweight SQLite user persistence.
Auto-creates database and tables on first import.

User fields:
- id (UUID)
- username
- email
- password_hash (bcrypt)
- role (admin | operator | viewer)
- created_at
- last_login
"""

import os
import sqlite3
import uuid
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional, List

logger = logging.getLogger("nexus.auth.models")

# Database path — inside nexus-core/
DB_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)
DB_PATH = os.path.join(DB_DIR, "nexus_auth.db")


# =============================================================================
# USER MODEL
# =============================================================================

@dataclass
class User:
    """NEXUS user account."""
    id: str
    username: str
    email: str
    password_hash: str
    role: str  # admin | operator | viewer
    created_at: str
    last_login: Optional[str] = None

    def to_dict(self) -> dict:
        """Safe user data — NO password hash."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at,
            "last_login": self.last_login,
        }


# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

def _get_connection() -> sqlite3.Connection:
    """Get SQLite connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create users table if not exists."""
    conn = _get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'viewer',
                created_at TEXT NOT NULL,
                last_login TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token_hash TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                revoked INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        conn.commit()
        logger.info(f"Auth database initialized: {DB_PATH}")
    finally:
        conn.close()


def _row_to_user(row: sqlite3.Row) -> User:
    """Convert SQLite row to User dataclass."""
    return User(
        id=row["id"],
        username=row["username"],
        email=row["email"],
        password_hash=row["password_hash"],
        role=row["role"],
        created_at=row["created_at"],
        last_login=row["last_login"],
    )


# =============================================================================
# CRUD OPERATIONS
# =============================================================================

def create_user(username: str, email: str, password_hash: str, role: str = "viewer") -> User:
    """Create a new user. Raises ValueError if username/email exists."""
    user_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    conn = _get_connection()
    try:
        conn.execute(
            "INSERT INTO users (id, username, email, password_hash, role, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username.lower(), email.lower(), password_hash, role, created_at)
        )
        conn.commit()
        logger.info(f"User created: {username} (role={role})")
        return User(
            id=user_id,
            username=username.lower(),
            email=email.lower(),
            password_hash=password_hash,
            role=role,
            created_at=created_at,
        )
    except sqlite3.IntegrityError as e:
        raise ValueError(f"User already exists: {e}")
    finally:
        conn.close()


def get_user_by_username(username: str) -> Optional[User]:
    """Get user by username."""
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username.lower(),)
        ).fetchone()
        return _row_to_user(row) if row else None
    finally:
        conn.close()


def get_user_by_email(email: str) -> Optional[User]:
    """Get user by email."""
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email.lower(),)
        ).fetchone()
        return _row_to_user(row) if row else None
    finally:
        conn.close()


def get_user_by_id(user_id: str) -> Optional[User]:
    """Get user by ID."""
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return _row_to_user(row) if row else None
    finally:
        conn.close()


def update_last_login(user_id: str):
    """Update user's last login timestamp."""
    conn = _get_connection()
    try:
        conn.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), user_id)
        )
        conn.commit()
    finally:
        conn.close()


def get_user_count() -> int:
    """Get total number of users."""
    conn = _get_connection()
    try:
        row = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()
        return row["cnt"] if row else 0
    finally:
        conn.close()


# =============================================================================
# REFRESH TOKEN PERSISTENCE
# =============================================================================

def store_refresh_token(user_id: str, token_hash: str, expires_at: str):
    """Store a refresh token hash."""
    conn = _get_connection()
    try:
        conn.execute(
            "INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), user_id, token_hash, expires_at,
             datetime.now(timezone.utc).isoformat())
        )
        conn.commit()
    finally:
        conn.close()


def get_refresh_token(token_hash: str) -> Optional[dict]:
    """Get refresh token by hash."""
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM refresh_tokens WHERE token_hash = ? AND revoked = 0",
            (token_hash,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def revoke_refresh_token(token_hash: str):
    """Revoke a refresh token."""
    conn = _get_connection()
    try:
        conn.execute(
            "UPDATE refresh_tokens SET revoked = 1 WHERE token_hash = ?",
            (token_hash,)
        )
        conn.commit()
    finally:
        conn.close()


def revoke_all_user_tokens(user_id: str):
    """Revoke all refresh tokens for a user."""
    conn = _get_connection()
    try:
        conn.execute(
            "UPDATE refresh_tokens SET revoked = 1 WHERE user_id = ?",
            (user_id,)
        )
        conn.commit()
    finally:
        conn.close()


# =============================================================================
# INIT ON IMPORT
# =============================================================================
init_db()
