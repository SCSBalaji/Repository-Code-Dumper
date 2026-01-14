"""
Middleware module for Repository Code Dumper.
Handles authentication, rate limiting, and request tracking.
"""

import time
import uuid
from collections import defaultdict
from typing import Callable, Dict

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .config import (
    ENABLE_API_AUTH,
    CODE_DUMPER_API_KEY,
    RATE_LIMIT_ENABLED,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW,
)


# Request ID header name
REQUEST_ID_HEADER = "X-Request-ID"


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware to add request tracking with correlation IDs."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get or generate request ID
        request_id = request.headers.get(REQUEST_ID_HEADER)
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Store request ID in request state for use in handlers
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers[REQUEST_ID_HEADER] = request_id
        
        return response


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Middleware for optional API key authentication."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip authentication if disabled
        if not ENABLE_API_AUTH:
            return await call_next(request)
        
        # Skip authentication for health endpoints
        if request.url.path in ["/", "/health"]:
            return await call_next(request)
        
        # Check for API key
        api_key = request.headers.get("X-API-Key")
        
        if not api_key:
            raise HTTPException(
                status_code=401,
                detail={
                    "error_code": "MISSING_API_KEY",
                    "error_type": "authentication_error",
                    "message": "API key is required. Provide it in the X-API-Key header.",
                }
            )
        
        if api_key != CODE_DUMPER_API_KEY:
            raise HTTPException(
                status_code=403,
                detail={
                    "error_code": "INVALID_API_KEY",
                    "error_type": "authentication_error",
                    "message": "Invalid API key provided.",
                }
            )
        
        return await call_next(request)


# Simple in-memory rate limiter
class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        # Use X-Forwarded-For if available, otherwise use client host
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _cleanup_old_requests(self, client_id: str, now: float) -> None:
        """Remove requests outside the current window."""
        cutoff = now - self.window_seconds
        self.requests[client_id] = [
            t for t in self.requests[client_id] if t > cutoff
        ]
    
    def is_allowed(self, request: Request) -> bool:
        """Check if the request is allowed under rate limits."""
        client_id = self._get_client_id(request)
        now = time.time()
        
        self._cleanup_old_requests(client_id, now)
        
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        
        self.requests[client_id].append(now)
        return True
    
    def get_remaining(self, request: Request) -> int:
        """Get remaining requests for a client."""
        client_id = self._get_client_id(request)
        now = time.time()
        self._cleanup_old_requests(client_id, now)
        return max(0, self.max_requests - len(self.requests[client_id]))


# Global rate limiter instance
rate_limiter = RateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting if disabled
        if not RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Skip rate limiting for health endpoints
        if request.url.path in ["/", "/health"]:
            return await call_next(request)
        
        if not rate_limiter.is_allowed(request):
            raise HTTPException(
                status_code=429,
                detail={
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "error_type": "rate_limit_error",
                    "message": f"Rate limit exceeded. Maximum {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds.",
                }
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = rate_limiter.get_remaining(request)
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_REQUESTS)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(RATE_LIMIT_WINDOW)
        
        return response
