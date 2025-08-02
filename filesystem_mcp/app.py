"""
Filesystem MCP - Main application module.

This module initializes the FastMCP 2.10 application and sets up logging.
"""

import logging
import logging.config
import os
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, status
from mcp import Application, FastMCP, FastMCPConfig
from pydantic import BaseModel, Field

# Configure logging
logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "INFO",
            "stream": "ext://sys.stdout"
        }
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True
        },
        "uvicorn": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False
        }
    }
})

logger = logging.getLogger(__name__)

# Initialize FastMCP 2.10 application
mcp_config = FastMCPConfig(
    name="filesystem-mcp",
    version="0.1.0",
    description="FastMCP 2.10 compliant MCP server for file system operations",
    license_info={"name": "MIT"},
    contact={
        "name": "Sandra Schimanovich",
        "email": "sandra@example.com"
    },
    servers=[{"url": "http://localhost:8000"}]
)

# Create FastAPI and FastMCP instances
fastapi_app = FastAPI(
    title="Filesystem MCP",
    description="FastMCP 2.10 compliant MCP server for file system operations",
    version="0.1.0"
)

app = FastMCP(
    fastapi_app=fastapi_app,
    config=mcp_config
)

# Add health check endpoint
@app.get("/health", include_in_schema=False)
async def health_check() -> Dict[str, str]:
    """Health check endpoint.
    
    Returns:
        Dict with status information
    """
    return {
        "status": "ok",
        "service": "filesystem-mcp",
        "version": "0.1.0"
    }

# Add error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "code": exc.status_code,
            "message": str(exc.detail),
            "path": request.url.path
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle all other exceptions."""
    logger.exception("Unhandled exception occurred")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "code": "internal_server_error",
            "message": "An internal server error occurred",
            "path": request.url.path
        }
    )

# Import and register tools
from .tools import register_tools  # noqa
register_tools(app)

# Add startup event handler
@fastapi_app.on_event("startup")
async def startup_event():
    """Run startup tasks."""
    logger.info("Starting Filesystem MCP server...")
    logger.info(f"Registered tools: {', '.join(app.list_tools().keys())}")

# Add shutdown event handler
@fastapi_app.on_event("shutdown")
async def shutdown_event():
    """Run shutdown tasks."""
    logger.info("Shutting down Filesystem MCP server...")
