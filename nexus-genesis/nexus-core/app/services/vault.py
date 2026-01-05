"""
NEXUS Vault - Secret Management Module
========================================

Google Secret Manager integration for secure credential storage.
All API keys and sensitive data fetched at runtime from Secret Manager.

IMMUTABLE LAW: No secrets in code. All secrets from Secret Manager.
"""

import logging
import sys
from typing import Dict, Optional

from google.api_core.exceptions import GoogleAPICallError
from google.cloud import secretmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("nexus.vault")


# =============================================================================
# CONFIGURATION
# =============================================================================

PROJECT_ID = "nexus-dyron-777"

# Initialize Secret Manager Client
try:
    client = secretmanager.SecretManagerServiceClient()
except Exception as e:
    logger.critical(f"Failed to initialize Secret Manager Client: {e}")
    sys.exit(1)


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
        SystemExit: If the secret cannot be retrieved, the system STOPS.
    """
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/{version_id}"
    
    try:
        logger.info(f"Accessing secret: {secret_id}")
        response = client.access_secret_version(request={"name": name})
        payload = response.payload.data.decode("UTF-8")
        return payload
    except GoogleAPICallError as e:
        logger.critical(f"FATAL: Could not retrieve secret '{secret_id}': {e}")
        sys.exit(1) # STOP THE SYSTEM
    except Exception as e:
        logger.critical(f"FATAL: Unexpected error accessing vault for '{secret_id}': {e}")
        sys.exit(1) # STOP THE SYSTEM
