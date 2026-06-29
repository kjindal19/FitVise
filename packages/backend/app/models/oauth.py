"""OAuth 2.1 entities (PRD §4.2) — present only in multi_user / managed modes.

Tokens are stored hashed; only the hash is persisted so a DB leak does not
expose live bearer tokens. PKCE (S256) is required on every authorization-code
grant (PRD §3.3).
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, created_at_column, pk_column


class OAuthClient(Base):
    __tablename__ = "oauth_clients"

    id: Mapped[str] = pk_column()
    client_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    client_secret_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    # dcr | cimd | preconfigured
    registration_type: Mapped[str] = mapped_column(String(16), nullable=False, default="dcr")
    redirect_uris: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[dt.datetime] = created_at_column()


class OAuthGrant(Base):
    __tablename__ = "oauth_grants"

    id: Mapped[str] = pk_column()
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    client_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    # Authorization-code exchange material
    code_hash: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    code_challenge: Mapped[str | None] = mapped_column(String(255), nullable=True)
    code_challenge_method: Mapped[str | None] = mapped_column(String(8), nullable=True)  # S256
    redirect_uri: Mapped[str | None] = mapped_column(String(512), nullable=True)
    scopes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    issued_at: Mapped[dt.datetime] = created_at_column()
    expires_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    id: Mapped[str] = pk_column()
    grant_id: Mapped[str | None] = mapped_column(ForeignKey("oauth_grants.id"), nullable=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    client_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    access_token_hash: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    refresh_token_hash: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    scopes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Refresh-token rotation chain (PRD §3.2 / §3.6).
    rotated_from: Mapped[str | None] = mapped_column(String(36), nullable=True)
    revoked_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[dt.datetime] = created_at_column()
