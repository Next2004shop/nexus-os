"""
NEXUS Rate Limiter - Unit Tests
=================================

Tests the in-memory token bucket rate limiter.
"""

import pytest
import sys
import os
import time

# Ensure project root is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import directly from main since rate limiter is defined there
# We need to test the RateLimiter class independently
from app.main import RateLimiter


# =============================================================================
# RATE LIMITER TESTS
# =============================================================================

class TestRateLimiter:
    """Tests for the RateLimiter class."""
    
    def test_allows_requests_within_limit(self):
        """Requests within the limit should be allowed."""
        limiter = RateLimiter()
        
        # Trade limit: 10 req/min
        for i in range(10):
            assert limiter.check("trade", "192.168.1.1") is True
    
    def test_blocks_requests_exceeding_limit(self):
        """Requests exceeding the limit should be blocked."""
        limiter = RateLimiter()
        
        # Trade limit: 10 req/min — exhaust them
        for i in range(10):
            limiter.check("trade", "192.168.1.1")
        
        # 11th request should be blocked
        assert limiter.check("trade", "192.168.1.1") is False
    
    def test_different_ips_independent(self):
        """Different IPs should have independent rate limits."""
        limiter = RateLimiter()
        
        # Exhaust limit for IP 1
        for i in range(10):
            limiter.check("trade", "192.168.1.1")
        
        # IP 2 should still be allowed
        assert limiter.check("trade", "192.168.1.2") is True
    
    def test_different_groups_independent(self):
        """Different endpoint groups should have independent limits."""
        limiter = RateLimiter()
        
        # Exhaust trade limit
        for i in range(10):
            limiter.check("trade", "192.168.1.1")
        
        # AI endpoint should still work (different group)
        assert limiter.check("ai", "192.168.1.1") is True
    
    def test_kill_has_lower_limit(self):
        """Kill endpoint should have 5 req/min limit."""
        limiter = RateLimiter()
        
        for i in range(5):
            assert limiter.check("kill", "192.168.1.1") is True
        
        # 6th should be blocked
        assert limiter.check("kill", "192.168.1.1") is False
    
    def test_default_group_limit(self):
        """Unknown group should use default limit (60 req/min)."""
        limiter = RateLimiter()
        
        for i in range(60):
            assert limiter.check("unknown_endpoint", "192.168.1.1") is True
        
        assert limiter.check("unknown_endpoint", "192.168.1.1") is False
    
    def test_has_expected_groups(self):
        """Rate limiter should have all expected groups configured."""
        limiter = RateLimiter()
        
        expected_groups = ["trade", "kill", "auth", "ai", "default"]
        for group in expected_groups:
            assert group in limiter.limits, f"Missing rate limit group: {group}"
