import time
import logging
from collections import defaultdict

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("NexusSecurity")

class NexusSecurity:
    def __init__(self):
        self.lockdown_mode = False
        self.ip_whitelist = ["127.0.0.1", "localhost", "::1"]
        self.request_log = defaultdict(list)
        self.failed_logins = defaultdict(int)
        self.MAX_REQUESTS_PER_MINUTE = 60
        self.MAX_FAILED_LOGINS = 3
        logger.info("🛡️ NEXUS SECURITY: ONLINE (DEFENSIVE MODE)")

    def check_request(self, ip_address, endpoint):
        """
        Analyzes incoming requests for anomalies.
        Returns True if safe, False if blocked.
        """
        if self.lockdown_mode:
            logger.warning(f"BLOCKED request from {ip_address} (LOCKDOWN ACTIVE)")
            return False

        current_time = time.time()
        
        # 1. Rate Limiting (DDoS Protection)
        self.request_log[ip_address] = [t for t in self.request_log[ip_address] if current_time - t < 60]
        self.request_log[ip_address].append(current_time)
        
        if len(self.request_log[ip_address]) > self.MAX_REQUESTS_PER_MINUTE:
            logger.warning(f"Rate Limit Exceeded for {ip_address}. Blocking.")
            return False

        # 2. Anomaly Detection (Mock Logic)
        # If accessing sensitive endpoints rapidly
        if endpoint == "/withdraw" and len(self.request_log[ip_address]) > 5:
             logger.critical(f"Suspicious Withdrawal Activity from {ip_address}. TRIGGERING LOCKDOWN.")
             self.trigger_lockdown("Suspicious Withdrawal Activity")
             return False

        return True

    def record_failed_login(self, ip_address):
        """Tracks failed logins to prevent Brute Force."""
        self.failed_logins[ip_address] += 1
        if self.failed_logins[ip_address] >= self.MAX_FAILED_LOGINS:
            logger.critical(f"Brute Force Detected from {ip_address}. Blocking IP.")
            return False # IP Blocked
        return True

    def trigger_lockdown(self, reason):
        """Freezes all critical operations."""
        self.lockdown_mode = True
        logger.critical(f"🚨 SYSTEM LOCKDOWN INITIATED: {reason}")
        # In a real system, this would email the admin and freeze funds.

    def lift_lockdown(self):
        self.lockdown_mode = False
        logger.info("System Lockdown Lifted. Operations Normal.")

security = NexusSecurity()
