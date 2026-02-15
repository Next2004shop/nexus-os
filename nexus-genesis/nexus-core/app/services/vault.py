"""
NEXUS Vault - Secret Management Module
========================================

Google Secret Manager integration for secure credential storage.
All API keys and sensitive data fetched at runtime from Secret Manager.

IMMUTABLE LAW: No secrets in code. All secrets from Secret Manager.

UPGRADE: Removed sys.exit() crash behavior. Now raises exceptions for
callers to handle gracefully. Lazy client initialization prevents
import-time crashes.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger("nexus.vault")


# =============================================================================
# CUSTOM EXCEPTIONS
# =============================================================================

class VaultError(Exception):
    """Base exception for vault operations."""
    pass


class VaultInitError(VaultError):
    """Raised when Secret Manager client cannot be initialized."""
    def __init__(self, original_error: Exception):
        self.original_error = original_error
        super().__init__(f"Failed to initialize Secret Manager Client: {original_error}")


class SecretRetrievalError(VaultError):
    """Raised when a secret cannot be retrieved from Secret Manager."""
    def __init__(self, secret_id: str, original_error: Exception):
        self.secret_id = secret_id
        self.original_error = original_error
        super().__init__(f"Could not retrieve secret '{secret_id}': {original_error}")


# =============================================================================
# CONFIGURATION
# =============================================================================

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "nexus-dyron-777")


# =============================================================================
# LAZY CLIENT INITIALIZATION
# =============================================================================

_client = None


def _get_client():
    """
    Lazily initialize Secret Manager client.
    
    Raises VaultInitError if initialization fails.
    Does NOT crash the process.
    """
    global _client
    if _client is not None:
        return _client
    
    try:
        from google.cloud import secretmanager
        _client = secretmanager.SecretManagerServiceClient()
        logger.info("Secret Manager client initialized")
        return _client
    except Exception as e:
        logger.critical(f"Failed to initialize Secret Manager Client: {e}")
        raise VaultInitError(e)


# =============================================================================
# SECRET RETRIEVAL
# =============================================================================

def get_secret(secret_id: str, version_id: str = "latest") -> str:
    """
    Fetches a secret from Google Secret Manager.
    
    Args:
        secret_id (str): The ID of the secret to retrieve.
        version_id (str): The version of the secret (default: "latest").
        
    Returns:
        str: The secret payload.
        
    Raises:
        SecretRetrievalError: If the secret cannot be retrieved.
        VaultInitError: If the Secret Manager client cannot be initialized.
    """
    client = _get_client()
    
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/{version_id}"
    
    try:
        logger.info(f"Accessing secret: {secret_id}")
        response = client.access_secret_version(request={"name": name})
        payload = response.payload.data.decode("UTF-8")
        return payload
    except Exception as e:
        logger.critical(f"FATAL: Could not retrieve secret '{secret_id}': {e}")
        raise SecretRetrievalError(secret_id, e)
