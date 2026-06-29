"""Resolve the authenticated FitVise user for an MCP request.

Every MCP tool call is scoped to exactly one user (PRD §3.3). Resolution:
- single_user : the sole provisioned user (no token needed; stdio + static key).
- single_user with FITVISE_MCP_API_KEY set: also accept the static key.
- multi_user / managed : Bearer access token issued by the OAuth AS; we hash it
  and look it up in oauth_tokens, enforcing expiry/revocation.

Two layers cooperate in multi-user mode:
- ``FitViseTokenVerifier`` runs at the transport (wired into FastMCP). It makes
  the MCP endpoint reply 401 + ``WWW-Authenticate`` to unauthenticated clients
  so OAuth-capable connectors (claude.ai, mcp-remote) discover and run the flow,
  and it populates the request's auth context with the verified token.
- ``resolve_user`` runs inside every tool as the in-tool isolation chokepoint
  (defense in depth) — it re-validates the forwarded bearer against the DB and
  returns the owning ``User`` that all queries are scoped to.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session

from app.auth.security import constant_time_equals, hash_token
from app.config import settings
from app.db.base import SessionLocal
from app.models.oauth import OAuthToken
from app.models.user import User


class MCPAuthError(Exception):
    """Raised when a request cannot be resolved to a user (→ UNAUTHORIZED)."""


def _bearer(headers: dict[str, str]) -> str | None:
    auth = headers.get("authorization") or headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return None


def _token_to_user(db: Session, token: str) -> User:
    """Validate an opaque OAuth bearer against oauth_tokens and return its owner.

    Shared by the transport-level verifier and the in-tool ``resolve_user`` so a
    token is accepted or rejected by exactly one set of rules.
    """
    record = (
        db.query(OAuthToken)
        .filter(OAuthToken.access_token_hash == hash_token(token))
        .first()
    )
    if record is None or record.revoked_at is not None:
        raise MCPAuthError("Invalid or revoked token")
    if record.expires_at <= dt.datetime.now(dt.timezone.utc):
        raise MCPAuthError("Token expired")
    user = db.get(User, record.user_id)
    if user is None or user.deleted_at is not None:
        raise MCPAuthError("User not found")
    return user


def resolve_user(db: Session, headers: dict[str, str]) -> User:
    token = _bearer(headers)

    if not settings.is_multi_user:
        # Optional static-key gate for local stdio remote exposure.
        if settings.mcp_api_key:
            supplied = token or headers.get("x-api-key") or ""
            if not constant_time_equals(supplied, settings.mcp_api_key):
                raise MCPAuthError("Invalid or missing MCP API key")
        user = db.query(User).filter(User.deleted_at.is_(None)).first()
        if user is None:
            raise MCPAuthError("No user provisioned")
        return user

    # multi_user / managed — OAuth bearer token required.
    if not token:
        raise MCPAuthError("Missing OAuth bearer token")
    return _token_to_user(db, token)


class FitViseTokenVerifier:
    """MCP ``TokenVerifier`` for the Streamable HTTP transport (multi-user only).

    FastMCP calls this for every request that carries a bearer token; returning
    ``None`` makes the transport emit 401 + ``WWW-Authenticate`` pointing at the
    Protected Resource Metadata, which is what triggers a connector's OAuth flow.
    The returned ``AccessToken`` is placed on the request auth context.
    """

    async def verify_token(self, token: str):  # -> mcp AccessToken | None
        from mcp.server.auth.provider import AccessToken

        with SessionLocal() as db:
            try:
                user = _token_to_user(db, token)
            except MCPAuthError:
                return None
            record = (
                db.query(OAuthToken)
                .filter(OAuthToken.access_token_hash == hash_token(token))
                .first()
            )
            return AccessToken(
                token=token,
                client_id=record.client_id,
                scopes=record.scopes or [],
                expires_at=int(record.expires_at.timestamp()),
                subject=user.id,
            )
