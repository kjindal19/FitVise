"""Crypto + token helpers shared by web auth and the OAuth AS.

- App/web sessions use short-lived HS256 JWTs signed with FITVISE_SECRET_KEY.
- OAuth access/refresh tokens are opaque random strings; only their SHA-256
  hash is stored (see models/oauth.py).
- Passwords use bcrypt (multi_user / managed only).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import secrets

import bcrypt
import jwt

from app.config import settings

ALGORITHM = "HS256"


# ---- Passwords -----------------------------------------------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("ascii"))
    except (ValueError, TypeError):
        return False


# ---- App/web JWTs --------------------------------------------------
def create_access_token(user_id: str, *, extra: dict | None = None, ttl: int | None = None) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int((now + dt.timedelta(seconds=ttl or settings.access_token_ttl)).timestamp()),
        "iss": settings.issuer,
        "typ": "app",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM], issuer=settings.issuer)


# ---- Opaque token hashing (OAuth + static keys) --------------------
def new_opaque_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)
