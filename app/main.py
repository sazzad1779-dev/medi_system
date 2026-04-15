"""
Main FastAPI Application Entry Point.
"""

import structlog
import logging
import sys
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.routes import prescriptions, review, health
from app.api.middleware.logging_middleware import LoggingMiddleware
from app.config import settings

# 1. Configure Structured Logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

app = FastAPI(
    title=getattr(settings, "APP_NAME", "Prescription System"),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 2. Add Middleware
app.add_middleware(LoggingMiddleware)

# 3. Include Routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(prescriptions.router, prefix="/api/v1")
app.include_router(review.router, prefix="/api/v1")

# 4. Exception Handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    structlog.get_logger().error(
        "unhandled_exception",
        path=request.url.path,
        error=str(exc),
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please contact support."}
    )

@app.on_event("startup")
async def startup_event():
    structlog.get_logger().info("app_starting", env=settings.APP_ENV)

@app.get("/")
async def root():
    return {"message": "Welcome to the Prescription Extraction System API"}
