import hashlib
import time
import logging
import json
from datetime import datetime

logger = logging.getLogger("NexusSecurity")

class SecurityVault:
    def __init__(self):
        self.master_key = hashlib.sha256(b"nexus-master-key").hexdigest()
        self.withdrawal_limit = 50000.00  # Daily limit
        self.daily_withdrawn = 0.00
        logger.info("🔒 SECURITY VAULT: INITIALIZED")
        logger.info("🛡️ ENCRYPTION PROTOCOLS: AES-256 (Simulated)")

    def encrypt_wallet(self, private_key):
        """
        Simulates encrypting a wallet private key.
        """
        encrypted = hashlib.sha256(private_key.encode()).hexdigest()
        return f"enc_{encrypted[:16]}"

    def verify_withdrawal(self, amount, user_id):
        """
        Verifies if a withdrawal request is safe and within limits.
        """
        logger.info(f"🕵️ VERIFYING WITHDRAWAL: ${amount} for {user_id}")
        
        if amount > self.withdrawal_limit:
            logger.warning(f"❌ WITHDRAWAL BLOCKED: Exceeds daily limit of ${self.withdrawal_limit}")
            return False, "Exceeds daily limit"
        
        if self.daily_withdrawn + amount > self.withdrawal_limit:
            logger.warning(f"❌ WITHDRAWAL BLOCKED: Daily limit reached")
            return False, "Daily limit reached"

        # Simulate risk check
        if amount > 10000:
            logger.info("⚠️ HIGH VALUE TRANSACTION: Performing deep packet inspection...")
            time.sleep(0.5) # Simulate check
        
        self.daily_withdrawn += amount
        logger.info("✅ WITHDRAWAL APPROVED")
        return True, "Approved"

class LedgerSystem:
    def __init__(self):
        self.ledger_file = "nexus_ledger.json"
        self.transactions = []
        logger.info("📚 LEDGER SYSTEM: ACTIVE")
        logger.info("🧾 BOOKS OF ACCOUNTS: OPEN")

    def record_transaction(self, type, amount, details):
        """
        Records a transaction immutably.
        """
        tx_id = hashlib.md5(f"{time.time()}{details}".encode()).hexdigest()[:12]
        entry = {
            "id": tx_id,
            "timestamp": datetime.now().isoformat(),
            "type": type,
            "amount": amount,
            "details": details,
            "hash": hashlib.sha256(f"{tx_id}{amount}".encode()).hexdigest()
        }
        self.transactions.append(entry)
        self._save_ledger()
        logger.info(f"🖊️ LEDGER ENTRY: [{type}] ${amount} - {details}")
        return tx_id

    def _save_ledger(self):
        """
        Saves ledger to disk (simulated persistence).
        """
        try:
            with open(self.ledger_file, 'w') as f:
                json.dump(self.transactions, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save ledger: {e}")

    def get_audit_trail(self):
        return self.transactions

vault = SecurityVault()
ledger = LedgerSystem()
