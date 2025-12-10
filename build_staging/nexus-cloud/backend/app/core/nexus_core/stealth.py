import os
import logging
from cryptography.fernet import Fernet
import shutil

logger = logging.getLogger("NexusStealth")

class StealthVault:
    """
    MODULE G: STEALTH PRIVACY LAYER
    Responsibility: Encryption, Zero-Trace, and Data Wiping.
    """
    def __init__(self, key_path="nexus.key"):
        self.key_path = key_path
        self.key = self._load_or_generate_key()
        self.cipher = Fernet(self.key)

    def _load_or_generate_key(self):
        if os.path.exists(self.key_path):
            with open(self.key_path, "rb") as key_file:
                return key_file.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_path, "wb") as key_file:
                key_file.write(key)
            return key

    def encrypt(self, data: str) -> bytes:
        return self.cipher.encrypt(data.encode())

    def decrypt(self, token: bytes) -> str:
        return self.cipher.decrypt(token).decode()

class BurnProtocol:
    """
    Responsibility: Securely wipe traces.
    """
    @staticmethod
    def execute_burn():
        """Wipes logs and chat history."""
        targets = ["backend.log", "nexus_chat_history.json"]
        wiped = []
        
        for target in targets:
            if os.path.exists(target):
                try:
                    # Secure overwrite (simplified)
                    file_size = os.path.getsize(target)
                    with open(target, "wb") as f:
                        f.write(os.urandom(file_size))
                    os.remove(target)
                    wiped.append(target)
                except Exception as e:
                    logger.error(f"Failed to burn {target}: {e}")
                    
        return wiped
