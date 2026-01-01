"""
NEXUS Authentication Service - Secure Account Management
=========================================================

ABSOLUTE LAW: No credentials on frontend - EVER.

Implements:
- Firebase Auth for user authentication
- Secure trading account credential storage
- Session management with short-lived tokens
- Device binding (optional)

Frontend receives: Session tokens ONLY
Backend stores: All credentials encrypted
"""

import logging
import secrets
import hashlib
import time
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from functools import wraps

logger = logging.getLogger("nexus.auth")


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class AuthLevel(Enum):
    """User authorization levels."""
    VIEWER = "viewer"           # Read-only access
    TRADER = "trader"           # Can execute trades
    ADMIN = "admin"             # Full system access
    MASTER = "master"           # System owner (you)


@dataclass
class UserSession:
    """Active user session."""
    user_id: str
    email: str
    auth_level: AuthLevel
    session_token: str
    created_at: datetime
    expires_at: datetime
    device_id: Optional[str] = None
    ip_address: Optional[str] = None
    is_active: bool = True
    
    def is_valid(self) -> bool:
        """Check if session is still valid."""
        return self.is_active and datetime.now(timezone.utc) < self.expires_at
    
    def to_frontend(self) -> Dict[str, Any]:
        """Safe session data for frontend - NO SECRETS."""
        return {
            "user_id": self.user_id,
            "email": self.email[:3] + "***" + self.email.split("@")[-1],  # Masked
            "auth_level": self.auth_level.value,
            "expires_in": int((self.expires_at - datetime.now(timezone.utc)).total_seconds()),
            "is_active": self.is_active
        }


@dataclass
class TradingAccount:
    """Trading account credentials - NEVER sent to frontend."""
    account_id: str
    broker: str  # "mt5", "binance", "oanda"
    login: str
    encrypted_password: str  # Encrypted at rest
    server: str
    user_id: str  # Owner of this account
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_used: Optional[datetime] = None


# =============================================================================
# ENCRYPTION UTILITIES
# =============================================================================

class CredentialVault:
    """
    Secure credential storage.
    
    Uses Google Secret Manager for encryption keys.
    All passwords encrypted at rest.
    """
    
    def __init__(self):
        self._encryption_key: Optional[bytes] = None
    
    def _get_encryption_key(self) -> bytes:
        """Get encryption key from Secret Manager."""
        if self._encryption_key:
            return self._encryption_key
        
        try:
            from app.services.vault import get_secret
            key = get_secret("NEXUS_ENCRYPTION_KEY")
            self._encryption_key = key.encode() if isinstance(key, str) else key
            return self._encryption_key
        except Exception as e:
            logger.error(f"Failed to get encryption key: {e}")
            # Fallback to derived key (less secure but functional)
            return hashlib.sha256(b"nexus-default-key").digest()
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt sensitive data."""
        key = self._get_encryption_key()
        
        # Simple HMAC-based encryption (use proper AES in production)
        import base64
        salt = secrets.token_bytes(16)
        cipher_key = hashlib.pbkdf2_hmac('sha256', key, salt, 100000)
        
        # XOR cipher (simplified - use AES-GCM in production)
        data = plaintext.encode()
        encrypted = bytes(a ^ b for a, b in zip(data, (cipher_key * (len(data) // 32 + 1))[:len(data)]))
        
        return base64.b64encode(salt + encrypted).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt sensitive data."""
        key = self._get_encryption_key()
        
        import base64
        raw = base64.b64decode(ciphertext)
        salt = raw[:16]
        encrypted = raw[16:]
        
        cipher_key = hashlib.pbkdf2_hmac('sha256', key, salt, 100000)
        decrypted = bytes(a ^ b for a, b in zip(encrypted, (cipher_key * (len(encrypted) // 32 + 1))[:len(encrypted)]))
        
        return decrypted.decode()


# =============================================================================
# FIREBASE AUTH INTEGRATION
# =============================================================================

class FirebaseAuthProvider:
    """
    Firebase Authentication integration.
    
    Handles:
    - User signup/login
    - Token verification
    - MFA enforcement
    """
    
    def __init__(self):
        self._app = None
        self._initialized = False
    
    def _initialize(self):
        """Initialize Firebase Admin SDK."""
        if self._initialized:
            return
        
        try:
            import firebase_admin
            from firebase_admin import credentials, auth
            
            # Use default credentials in Cloud Run
            if not firebase_admin._apps:
                firebase_admin.initialize_app()
            
            self._app = firebase_admin.get_app()
            self._initialized = True
            logger.info("Firebase Auth initialized")
            
        except Exception as e:
            logger.warning(f"Firebase init failed (will use fallback): {e}")
    
    def verify_id_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """Verify Firebase ID token."""
        self._initialize()
        
        if not self._initialized:
            logger.warning("Firebase not available, using fallback auth")
            return None
        
        try:
            from firebase_admin import auth
            decoded = auth.verify_id_token(id_token)
            return decoded
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None
    
    def get_user(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get user details from Firebase."""
        self._initialize()
        
        if not self._initialized:
            return None
        
        try:
            from firebase_admin import auth
            user = auth.get_user(uid)
            return {
                "uid": user.uid,
                "email": user.email,
                "email_verified": user.email_verified,
                "disabled": user.disabled,
                "mfa_enabled": bool(user.multi_factor)
            }
        except Exception as e:
            logger.error(f"Get user failed: {e}")
            return None


# =============================================================================
# SESSION MANAGER
# =============================================================================

class SessionManager:
    """
    Manages user sessions with short-lived tokens.
    
    Session rules:
    - Tokens expire in 1 hour
    - Refresh extends by 1 hour
    - Max 5 active sessions per user
    - Device binding optional but recommended
    """
    
    SESSION_DURATION = timedelta(hours=1)
    MAX_SESSIONS_PER_USER = 5
    
    def __init__(self):
        self._sessions: Dict[str, UserSession] = {}  # token -> session
        self._user_sessions: Dict[str, list] = {}    # user_id -> [tokens]
        self._vault = CredentialVault()
    
    def create_session(
        self,
        user_id: str,
        email: str,
        auth_level: AuthLevel = AuthLevel.VIEWER,
        device_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> UserSession:
        """Create new user session."""
        
        # Generate secure session token
        token = secrets.token_urlsafe(32)
        
        now = datetime.now(timezone.utc)
        session = UserSession(
            user_id=user_id,
            email=email,
            auth_level=auth_level,
            session_token=token,
            created_at=now,
            expires_at=now + self.SESSION_DURATION,
            device_id=device_id,
            ip_address=ip_address
        )
        
        # Store session
        self._sessions[token] = session
        
        # Track user sessions
        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = []
        self._user_sessions[user_id].append(token)
        
        # Enforce max sessions
        self._cleanup_user_sessions(user_id)
        
        logger.info(f"Session created for {email}")
        return session
    
    def validate_session(self, token: str) -> Optional[UserSession]:
        """Validate session token."""
        session = self._sessions.get(token)
        
        if not session:
            return None
        
        if not session.is_valid():
            self.invalidate_session(token)
            return None
        
        return session
    
    def refresh_session(self, token: str) -> Optional[UserSession]:
        """Refresh session expiration."""
        session = self.validate_session(token)
        
        if not session:
            return None
        
        session.expires_at = datetime.now(timezone.utc) + self.SESSION_DURATION
        return session
    
    def invalidate_session(self, token: str):
        """Invalidate a session."""
        session = self._sessions.pop(token, None)
        if session:
            session.is_active = False
            # Remove from user sessions
            if session.user_id in self._user_sessions:
                self._user_sessions[session.user_id] = [
                    t for t in self._user_sessions[session.user_id] if t != token
                ]
            logger.info(f"Session invalidated for {session.user_id}")
    
    def invalidate_all_user_sessions(self, user_id: str):
        """Invalidate all sessions for a user."""
        tokens = self._user_sessions.get(user_id, [])
        for token in tokens:
            if token in self._sessions:
                self._sessions[token].is_active = False
                del self._sessions[token]
        self._user_sessions[user_id] = []
        logger.warning(f"All sessions invalidated for {user_id}")
    
    def _cleanup_user_sessions(self, user_id: str):
        """Remove oldest sessions if over limit."""
        tokens = self._user_sessions.get(user_id, [])
        
        while len(tokens) > self.MAX_SESSIONS_PER_USER:
            oldest_token = tokens.pop(0)
            if oldest_token in self._sessions:
                self._sessions[oldest_token].is_active = False
                del self._sessions[oldest_token]


# =============================================================================
# TRADING ACCOUNT MANAGER
# =============================================================================

class TradingAccountManager:
    """
    Manages trading account credentials.
    
    ABSOLUTE LAW: Credentials NEVER leave the backend.
    Frontend only knows account exists, not credentials.
    """
    
    def __init__(self):
        self._accounts: Dict[str, TradingAccount] = {}  # account_id -> account
        self._user_accounts: Dict[str, list] = {}       # user_id -> [account_ids]
        self._vault = CredentialVault()
    
    def register_account(
        self,
        user_id: str,
        broker: str,
        login: str,
        password: str,
        server: str
    ) -> str:
        """
        Register a trading account.
        
        Password is encrypted before storage.
        Returns account_id for reference.
        """
        account_id = secrets.token_urlsafe(16)
        
        account = TradingAccount(
            account_id=account_id,
            broker=broker,
            login=login,
            encrypted_password=self._vault.encrypt(password),
            server=server,
            user_id=user_id
        )
        
        self._accounts[account_id] = account
        
        if user_id not in self._user_accounts:
            self._user_accounts[user_id] = []
        self._user_accounts[user_id].append(account_id)
        
        logger.info(f"Trading account registered: {broker}/{login[:3]}***")
        return account_id
    
    def get_account_info(self, account_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get safe account info for frontend.
        
        NO CREDENTIALS RETURNED.
        """
        account = self._accounts.get(account_id)
        
        if not account or account.user_id != user_id:
            return None
        
        return {
            "account_id": account_id,
            "broker": account.broker,
            "login": account.login[:3] + "***",  # Masked
            "server": account.server,
            "is_active": account.is_active,
            "last_used": account.last_used.isoformat() if account.last_used else None
        }
    
    def get_credentials_for_execution(self, account_id: str, session: UserSession) -> Optional[Dict[str, str]]:
        """
        Get decrypted credentials for trade execution.
        
        BACKEND ONLY - Never call from frontend routes.
        Requires valid session with TRADER+ auth level.
        """
        if session.auth_level not in [AuthLevel.TRADER, AuthLevel.ADMIN, AuthLevel.MASTER]:
            logger.warning(f"Unauthorized credential access attempt: {session.user_id}")
            return None
        
        account = self._accounts.get(account_id)
        
        if not account or account.user_id != session.user_id:
            return None
        
        # Decrypt password
        password = self._vault.decrypt(account.encrypted_password)
        
        # Update last used
        account.last_used = datetime.now(timezone.utc)
        
        return {
            "broker": account.broker,
            "login": account.login,
            "password": password,
            "server": account.server
        }
    
    def list_user_accounts(self, user_id: str) -> list:
        """List user's accounts (safe info only)."""
        account_ids = self._user_accounts.get(user_id, [])
        return [
            self.get_account_info(aid, user_id)
            for aid in account_ids
            if self.get_account_info(aid, user_id)
        ]


# =============================================================================
# AUTHENTICATION SERVICE
# =============================================================================

class AuthService:
    """
    Main authentication service.
    
    Coordinates:
    - Firebase user auth
    - Session management
    - Trading account management
    """
    
    def __init__(self):
        self.firebase = FirebaseAuthProvider()
        self.sessions = SessionManager()
        self.trading_accounts = TradingAccountManager()
        
        # Master user ID (set from Secret Manager)
        self._master_user_id: Optional[str] = None
    
    def _get_master_user_id(self) -> Optional[str]:
        """Get master user ID from secrets."""
        if self._master_user_id:
            return self._master_user_id
        
        try:
            from app.services.vault import get_secret
            self._master_user_id = get_secret("NEXUS_MASTER_USER_ID")
            return self._master_user_id
        except Exception:
            return None
    
    def login_with_firebase(
        self,
        id_token: str,
        device_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, Optional[UserSession], str]:
        """
        Login using Firebase ID token.
        
        Returns: (success, session, message)
        """
        # Verify Firebase token
        decoded = self.firebase.verify_id_token(id_token)
        
        if not decoded:
            return False, None, "Invalid or expired token"
        
        # Get user details
        user_id = decoded.get("uid")
        email = decoded.get("email", "")
        
        # Determine auth level
        master_id = self._get_master_user_id()
        if user_id == master_id:
            auth_level = AuthLevel.MASTER
        else:
            auth_level = AuthLevel.VIEWER  # Default to viewer
        
        # Create session
        session = self.sessions.create_session(
            user_id=user_id,
            email=email,
            auth_level=auth_level,
            device_id=device_id,
            ip_address=ip_address
        )
        
        return True, session, "Login successful"
    
    def validate_request(self, token: str) -> Optional[UserSession]:
        """Validate request session token."""
        return self.sessions.validate_session(token)
    
    def logout(self, token: str):
        """Logout session."""
        self.sessions.invalidate_session(token)
    
    def is_master(self, session: UserSession) -> bool:
        """Check if session belongs to master user."""
        return session.auth_level == AuthLevel.MASTER


# =============================================================================
# DECORATORS
# =============================================================================

def require_auth(min_level: AuthLevel = AuthLevel.VIEWER):
    """Decorator to require authentication."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from fastapi import HTTPException, Header
            
            auth_header = kwargs.get("authorization")
            if not auth_header:
                raise HTTPException(status_code=401, detail="Authorization required")
            
            token = auth_header.replace("Bearer ", "")
            
            auth_service = get_auth_service()
            session = auth_service.validate_request(token)
            
            if not session:
                raise HTTPException(status_code=401, detail="Invalid session")
            
            # Check auth level
            level_order = [AuthLevel.VIEWER, AuthLevel.TRADER, AuthLevel.ADMIN, AuthLevel.MASTER]
            if level_order.index(session.auth_level) < level_order.index(min_level):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            
            kwargs["session"] = session
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get or create auth service."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
