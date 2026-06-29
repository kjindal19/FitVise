"""Central configuration, sourced from FITVISE_* environment variables.

A single ``settings`` object is imported across the app. The deployment mode
(`single_user` | `multi_user` | `managed`) and DB type are the two switches
that change behaviour the most — everything reads off these.
"""
from __future__ import annotations

from enum import Enum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthMode(str, Enum):
    single_user = "single_user"
    multi_user = "multi_user"
    managed = "managed"


class DbType(str, Enum):
    sqlite = "sqlite"
    postgres = "postgres"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FITVISE_",
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- Core ----
    secret_key: str = "change-me-dev-secret"
    auth_mode: AuthMode = AuthMode.single_user
    base_url: str = "http://localhost:8000"
    port: int = 8000

    # ---- Database ----
    db_type: DbType = DbType.sqlite
    db_path: str = "/data/fitvise.sqlite3"
    db_url: str | None = None  # populated for postgres; overrides db_path

    # ---- MCP ----
    mcp_api_key: str | None = None

    # ---- OAuth (multi_user / managed) ----
    oauth_issuer_url: str | None = None
    oauth_signing_key: str | None = None

    # ---- Notifications / Web Push ----
    vapid_public_key: str | None = None
    vapid_private_key: str | None = None
    vapid_subject: str = "mailto:admin@example.com"
    default_timezone: str = "UTC"

    # ---- Token lifetimes (seconds) ----
    access_token_ttl: int = 60 * 60               # 1h app/web JWT
    oauth_access_token_ttl: int = 60 * 60         # 1h MCP access token
    oauth_refresh_token_ttl: int = 60 * 60 * 24 * 30  # 30d refresh token

    # ---- Derived helpers ----
    @property
    def is_multi_user(self) -> bool:
        return self.auth_mode in (AuthMode.multi_user, AuthMode.managed)

    @property
    def issuer(self) -> str:
        return (self.oauth_issuer_url or self.base_url).rstrip("/")

    @property
    def sqlalchemy_url(self) -> str:
        if self.db_type is DbType.postgres:
            if not self.db_url:
                raise RuntimeError("FITVISE_DB_URL is required when FITVISE_DB_TYPE=postgres")
            return self.db_url
        return f"sqlite:///{self.db_path}"

    @property
    def webpush_enabled(self) -> bool:
        return bool(self.vapid_public_key and self.vapid_private_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
