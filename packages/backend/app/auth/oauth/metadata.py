"""OAuth discovery documents (PRD §3.3).

- Protected Resource Metadata  (RFC 9728) → /.well-known/oauth-protected-resource
- Authorization Server Metadata (RFC 8414) → /.well-known/oauth-authorization-server

Both advertise PKCE S256 and Dynamic Client Registration so claude.ai-style
remote connectors can self-configure.
"""
from __future__ import annotations

from app.config import settings


def protected_resource_metadata() -> dict:
    base = settings.base_url.rstrip("/")
    return {
        "resource": f"{base}/mcp",
        "authorization_servers": [settings.issuer],
        "bearer_methods_supported": ["header"],
        "scopes_supported": ["fitvise.read", "fitvise.write"],
        "resource_documentation": f"{base}/docs",
    }


def authorization_server_metadata() -> dict:
    issuer = settings.issuer
    return {
        "issuer": issuer,
        "authorization_endpoint": f"{issuer}/oauth/authorize",
        "token_endpoint": f"{issuer}/oauth/token",
        "registration_endpoint": f"{issuer}/oauth/register",
        "revocation_endpoint": f"{issuer}/oauth/revoke",
        "scopes_supported": ["fitvise.read", "fitvise.write"],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["none", "client_secret_post"],
        "code_challenge_methods_supported": ["S256"],
    }
