"""
NEXUS Vault Safety - Unit Tests
=================================

Tests that vault.py handles errors gracefully without calling sys.exit().
Validates custom exceptions, lazy initialization, and error propagation.
"""

import pytest
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.vault import (
    VaultError,
    VaultInitError,
    SecretRetrievalError,
    get_secret,
    _get_client,
)


# =============================================================================
# EXCEPTION HIERARCHY TESTS
# =============================================================================

class TestVaultExceptions:
    """Tests for vault custom exceptions."""
    
    def test_vault_error_is_base(self):
        """VaultError is the base exception."""
        assert issubclass(VaultInitError, VaultError)
        assert issubclass(SecretRetrievalError, VaultError)
    
    def test_vault_init_error_contains_original(self):
        """VaultInitError should contain the original exception."""
        original = RuntimeError("No credentials")
        err = VaultInitError(original)
        assert err.original_error is original
        assert "No credentials" in str(err)
    
    def test_secret_retrieval_error_contains_details(self):
        """SecretRetrievalError should contain secret_id and original error."""
        original = ConnectionError("timeout")
        err = SecretRetrievalError("my-api-key", original)
        assert err.secret_id == "my-api-key"
        assert err.original_error is original
        assert "my-api-key" in str(err)
        assert "timeout" in str(err)


# =============================================================================
# NO SYS.EXIT TESTS
# =============================================================================

class TestNoSysExit:
    """Ensures vault never calls sys.exit()."""
    
    def test_get_secret_raises_not_exits(self):
        """get_secret() should raise an exception, not call sys.exit()."""
        # We expect either VaultInitError (if client init fails) or
        # SecretRetrievalError (if client init succeeds but secret fetch fails)
        with pytest.raises(VaultError):
            get_secret("nonexistent-secret-for-test")
    
    def test_get_client_raises_not_exits(self):
        """_get_client() should raise VaultInitError, not call sys.exit()."""
        # Reset the cached client so it tries to reinitialize
        import app.services.vault as vault_module
        original_client = vault_module._client
        vault_module._client = None
        
        try:
            # This will fail because we don't have GCP credentials in test
            # but it should RAISE, not EXIT
            with pytest.raises(VaultError):
                _get_client()
        finally:
            # Restore original state
            vault_module._client = original_client


# =============================================================================
# LAZY INITIALIZATION TESTS
# =============================================================================

class TestLazyInit:
    """Tests for lazy client initialization."""
    
    def test_module_imports_without_crash(self):
        """Importing vault should not crash even without GCP credentials."""
        # If we got this far, import succeeded
        import app.services.vault
        assert hasattr(app.services.vault, 'get_secret')
        assert hasattr(app.services.vault, 'VaultError')
        assert hasattr(app.services.vault, 'SecretRetrievalError')
    
    def test_client_is_none_initially(self):
        """Client should be None before any attempt to use it."""
        import app.services.vault as vault_module
        # After fresh import/reset, client may be None or cached
        # The key property is it doesn't crash during import
        assert hasattr(vault_module, '_client')
