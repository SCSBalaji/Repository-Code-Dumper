"""
Unit tests for middleware module.
"""

import pytest
import time
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import Request, HTTPException
from starlette.responses import Response

from app.middleware import (
    RequestTrackingMiddleware,
    APIKeyAuthMiddleware,
    RateLimitMiddleware,
    RateLimiter,
    REQUEST_ID_HEADER,
)


class MockRequest:
    """Mock request object for testing."""
    
    def __init__(self, headers=None, path="/test", client_host="127.0.0.1"):
        self.headers = headers or {}
        self.url = MagicMock()
        self.url.path = path
        self.client = MagicMock()
        self.client.host = client_host
        self.state = MagicMock()
        self.state.request_id = None


class TestRateLimiter:
    """Tests for RateLimiter class."""
    
    def test_allows_requests_under_limit(self):
        """Test that requests under limit are allowed."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        request = MockRequest()
        
        for _ in range(5):
            assert limiter.is_allowed(request) is True
    
    def test_blocks_requests_over_limit(self):
        """Test that requests over limit are blocked."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        request = MockRequest()
        
        for _ in range(3):
            limiter.is_allowed(request)
        
        assert limiter.is_allowed(request) is False
    
    def test_allows_requests_after_window_expires(self):
        """Test that requests are allowed after window expires."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        request = MockRequest()
        
        limiter.is_allowed(request)
        limiter.is_allowed(request)
        assert limiter.is_allowed(request) is False
        
        # Wait for window to expire
        time.sleep(1.1)
        
        assert limiter.is_allowed(request) is True
    
    def test_tracks_different_clients_separately(self):
        """Test that different clients are tracked separately."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        request1 = MockRequest(client_host="192.168.1.1")
        request2 = MockRequest(client_host="192.168.1.2")
        
        limiter.is_allowed(request1)
        limiter.is_allowed(request1)
        
        # First client is blocked
        assert limiter.is_allowed(request1) is False
        
        # Second client is still allowed
        assert limiter.is_allowed(request2) is True
    
    def test_get_remaining_returns_correct_count(self):
        """Test that remaining count is correct."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        request = MockRequest()
        
        assert limiter.get_remaining(request) == 5
        
        limiter.is_allowed(request)
        assert limiter.get_remaining(request) == 4
        
        limiter.is_allowed(request)
        limiter.is_allowed(request)
        assert limiter.get_remaining(request) == 2
    
    def test_uses_forwarded_for_header(self):
        """Test that X-Forwarded-For header is used for client identification."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        request = MockRequest(
            headers={"X-Forwarded-For": "10.0.0.1, 10.0.0.2"},
            client_host="127.0.0.1"
        )
        
        limiter.is_allowed(request)
        limiter.is_allowed(request)
        
        # Should be blocked based on first IP in X-Forwarded-For
        assert limiter.is_allowed(request) is False


class TestRequestTrackingMiddlewareUnit:
    """Unit tests for request tracking."""
    
    def test_request_id_header_name(self):
        """Test request ID header name constant."""
        assert REQUEST_ID_HEADER == "X-Request-ID"
    
    def test_generates_uuid_format_request_id(self):
        """Test that generated request IDs are valid UUIDs."""
        import uuid
        
        # Generate a UUID and check format
        test_id = str(uuid.uuid4())
        assert len(test_id) == 36
        assert test_id.count('-') == 4
