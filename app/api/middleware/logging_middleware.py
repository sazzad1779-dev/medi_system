"""
Middleware for structured logging of all API requests.
Uses structlog for JSON compatible logging.
"""

import time
import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log basic request/response info
        logger.info(
            "request_processed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            ip=request.client.host if request.client else "unknown"
        )
        
        return response
