"""
NEXUS Auth Enforcement - Unit Tests
=====================================

Tests the FastAPI Depends-based auth system.
Validates that protected endpoints reject unauthorized access
and allow authorized access with correct permission levels.
"""

import pytest
import sys
import os
import time

# Ensure project root is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.auth_service import (
    AuthLevel,
    UserSession,
    _extract_session,
    _check_level,
    _LEVEL_ORDER,
)


# =============================================================================
# SESSION EXTRACTION TESTS
# =============================================================================

class TestExtractSession:
    """Tests for the _extract_session helper."""
    
    def test_no_header_raises_401(self):
        """No Authorization header should raise 401."""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            _extract_session("")
        assert exc_info.value.status_code == 401
    
    def test_no_bearer_prefix_raises_401(self):
        """Authorization without 'Bearer ' prefix should raise 401."""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            _extract_session("Token abc123")
        assert exc_info.value.status_code == 401
    
    def test_invalid_token_raises_401(self):
        """An invalid token should raise 401 (no valid session)."""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            _extract_session("Bearer totally_fake_token_12345")
        assert exc_info.value.status_code == 401


# =============================================================================
# AUTH LEVEL CHECKS
# =============================================================================

class TestAuthLevelCheck:
    """Tests for auth level permission checking."""
    
    def _make_session(self, level: AuthLevel) -> UserSession:
        """Helper to create a test session."""
        return UserSession(
            user_id="test-user-001",
            email="test@nexus.ai",
            auth_level=level,
            session_token="test-token",
            created_at=time.time(),
            expires_at=time.time() + 3600,
        )
    
    def test_viewer_passes_viewer_check(self):
        """VIEWER should pass VIEWER-level check."""
        session = self._make_session(AuthLevel.VIEWER)
        # Should NOT raise
        _check_level(session, AuthLevel.VIEWER)
    
    def test_trader_passes_trader_check(self):
        """TRADER should pass TRADER-level check."""
        session = self._make_session(AuthLevel.TRADER)
        _check_level(session, AuthLevel.TRADER)
    
    def test_admin_passes_trader_check(self):
        """ADMIN should pass TRADER-level check (higher level)."""
        session = self._make_session(AuthLevel.ADMIN)
        _check_level(session, AuthLevel.TRADER)
    
    def test_master_passes_all_checks(self):
        """MASTER should pass all level checks."""
        session = self._make_session(AuthLevel.MASTER)
        for level in AuthLevel:
            _check_level(session, level)
    
    def test_viewer_fails_trader_check(self):
        """VIEWER should fail TRADER-level check."""
        from fastapi import HTTPException
        
        session = self._make_session(AuthLevel.VIEWER)
        with pytest.raises(HTTPException) as exc_info:
            _check_level(session, AuthLevel.TRADER)
        assert exc_info.value.status_code == 403
    
    def test_viewer_fails_admin_check(self):
        """VIEWER should fail ADMIN-level check."""
        from fastapi import HTTPException
        
        session = self._make_session(AuthLevel.VIEWER)
        with pytest.raises(HTTPException) as exc_info:
            _check_level(session, AuthLevel.ADMIN)
        assert exc_info.value.status_code == 403
    
    def test_trader_fails_admin_check(self):
        """TRADER should fail ADMIN-level check."""
        from fastapi import HTTPException
        
        session = self._make_session(AuthLevel.TRADER)
        with pytest.raises(HTTPException) as exc_info:
            _check_level(session, AuthLevel.ADMIN)
        assert exc_info.value.status_code == 403


# =============================================================================
# LEVEL ORDER VALIDATION
# =============================================================================

class TestLevelOrder:
    """Tests that the level hierarchy is correct."""
    
    def test_level_order(self):
        """Auth levels must be ordered: VIEWER < TRADER < ADMIN < MASTER."""
        assert _LEVEL_ORDER == [
            AuthLevel.VIEWER,
            AuthLevel.TRADER,
            AuthLevel.ADMIN,
            AuthLevel.MASTER,
        ]
    
    def test_all_levels_represented(self):
        """All AuthLevel values must be in the level order."""
        for level in AuthLevel:
            assert level in _LEVEL_ORDER, f"AuthLevel.{level.name} missing from _LEVEL_ORDER"
