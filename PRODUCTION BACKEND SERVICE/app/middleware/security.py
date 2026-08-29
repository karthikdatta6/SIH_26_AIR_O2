"""
backend/app/middleware/security.py
Enterprise-Grade Security, Observability, and Threat Mitigation Middleware Suite for AIRO2.

Features:
1. SecurityHeadersMiddleware: Implements HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy.
2. RateLimiterMiddleware: Sliding-window memory rate limiter defending against DoS/Brute-Force traffic surges.
3. RequestCorrelationMiddleware: Injects unique X-Request-ID and tracks high-resolution latency X-Response-Time-Ms.
4. PayloadSizeLimitMiddleware: Prevents buffer overflow and memory exhaustion DoS attacks by capping payload size.
"""

import time
import uuid
import logging
from collections import defaultdict
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

logger = logging.getLogger("airo2.security")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects institutional HTTP security headers on all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 1. Prevent MIME-sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # 2. Clickjacking mitigation (Allow self for embedded dashboard frames if needed)
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        
        # 3. Cross-Site Scripting (XSS) Filter
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # 4. Strict Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # 5. Restrict dangerous browser features
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # 6. HTTP Strict Transport Security (HSTS - 1 year)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # 7. Content Security Policy (Allows Leaflet tiles, CDN scripts, and inline styles safely)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self' https: data: blob: 'unsafe-inline' 'unsafe-eval'; "
            "img-src 'self' https: data: blob: https://*.tile.openstreetmap.org https://*.basemaps.cartocdn.com; "
            "connect-src 'self' https: https://api.open-meteo.com https://air-quality-api.open-meteo.com;"
        )
        
        return response


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window token rate limiter per client IP.
    Default: 120 requests per minute per IP address.
    """
    def __init__(self, app, requests_per_minute: int = 120):
        super().__init__(app)
        self.rpm = requests_per_minute
        self.clients = defaultdict(list)
        self.cleanup_interval = 60.0
        self.last_cleanup = time.time()

    def _cleanup_old_records(self, now: float):
        """Purges client records older than 60 seconds to prevent memory leaks."""
        if now - self.last_cleanup > self.cleanup_interval:
            for ip in list(self.clients.keys()):
                self.clients[ip] = [t for t in self.clients[ip] if now - t < 60.0]
                if not self.clients[ip]:
                    del self.clients[ip]
            self.last_cleanup = now

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Exclude static assets from rate limiting
        if request.url.path.startswith("/static") or request.url.path in ["/favicon.ico"]:
            return await call_next(request)
        
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        
        self._cleanup_old_records(now)
        
        # Filter timestamps within the 60-second window
        window_start = now - 60.0
        self.clients[client_ip] = [t for t in self.clients[client_ip] if t > window_start]
        
        if len(self.clients[client_ip]) >= self.rpm:
            logger.warning(f"[Security] Rate limit breached by client IP: {client_ip} on path: {request.url.path}")
            return JSONResponse(
                status_code=429,
                content={
                    "status": 429,
                    "error": "TooManyRequests",
                    "message": f"Rate limit of {self.rpm} requests per minute exceeded. Please back off.",
                    "retry_after_seconds": 30
                },
                headers={"Retry-After": "30"}
            )
        
        self.clients[client_ip].append(now)
        return await call_next(request)


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """Tracks latency, attaches unique correlation UUIDs, and structured audit logs."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start_time = time.perf_counter()
        
        # Attach request ID to request state
        request.state.request_id = req_id
        
        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(
                f"[Audit] {request.method} {request.url.path} | status=500 | duration={duration_ms:.2f}ms | req_id={req_id} | error={exc}"
            )
            raise exc
            
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        
        # Attach correlation headers
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
        
        # Structured audit logging
        client_ip = request.client.host if request.client else "anonymous"
        logger.info(
            f"[Audit] {request.method} {request.url.path} | status={response.status_code} | duration={duration_ms:.2f}ms | ip={client_ip} | req_id={req_id}"
        )
        
        return response


class PayloadSizeLimitMiddleware(BaseHTTPMiddleware):
    """Rejects incoming HTTP requests with bodies exceeding the maximum limit (Default: 2 MB)."""
    def __init__(self, app, max_payload_bytes: int = 2 * 1024 * 1024):
        super().__init__(app)
        self.max_bytes = max_payload_bytes

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_bytes:
            logger.warning(f"[Security] Rejected oversized payload ({content_length} bytes) from {request.client.host if request.client else 'unknown'}")
            return JSONResponse(
                status_code=413,
                content={
                    "status": 413,
                    "error": "PayloadTooLarge",
                    "message": f"Request body exceeds maximum permitted size of {self.max_bytes / (1024*1024):.1f} MB."
                }
            )
        return await call_next(request)
