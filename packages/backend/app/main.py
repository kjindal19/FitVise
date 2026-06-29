"""FitVise backend entrypoint.

Composes the REST API (/api/v1), the MCP server (/mcp, Streamable HTTP), the
OAuth 2.1 AS + discovery documents, and starts the notification scheduler. The
deployment mode (single_user | multi_user | managed) is read from config and
changes auth behaviour throughout.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.v1 import api_router
from app.api.v1.health import health as health_handler
from app.auth.oauth import metadata as oauth_metadata
from app.auth.oauth.router import router as oauth_router
from app.config import settings
from app.mcp.server import mcp_server
from app.notifications import scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fitvise")

# Build the MCP ASGI app once; this also wires its session manager.
mcp_app = mcp_server.streamable_http_app()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    async with mcp_server.session_manager.run():
        logger.info("FitVise %s up — mode=%s db=%s", __version__,
                    settings.auth_mode.value, settings.db_type.value)
        yield
    scheduler.shutdown()


app = FastAPI(
    title="FitVise API",
    version=__version__,
    description="Persistent data + logging layer for an AI fitness coach (MCP).",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # self-hosted; tighten via reverse proxy if needed
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API
app.include_router(api_router)

# Bare /health for load balancers / uptime checks (also at /api/v1/health).
app.add_api_route("/health", health_handler, methods=["GET"], tags=["health"])


# ---- OAuth discovery + endpoints (multi_user / managed) ------------
@app.get("/.well-known/oauth-protected-resource", tags=["oauth"])
def prm():
    return oauth_metadata.protected_resource_metadata()


@app.get("/.well-known/oauth-authorization-server", tags=["oauth"])
def asm():
    return oauth_metadata.authorization_server_metadata()


app.include_router(oauth_router)

# ---- MCP (Streamable HTTP) -----------------------------------------
# Endpoint is /mcp (requests to /mcp 307-redirect to /mcp/, preserving method).
app.mount("/mcp", mcp_app)


@app.get("/", tags=["meta"])
def root():
    return {
        "name": "FitVise",
        "version": __version__,
        "auth_mode": settings.auth_mode.value,
        "mcp_endpoint": f"{settings.base_url.rstrip('/')}/mcp",
        "docs": "/docs",
    }
