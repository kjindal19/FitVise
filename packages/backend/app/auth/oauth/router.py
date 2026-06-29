"""OAuth 2.1 Authorization Server endpoints (PRD §3.3 / §3.6).

Functional skeleton implementing the authorization-code + PKCE (S256) flow with
Dynamic Client Registration, refresh-token rotation, and revocation. The browser
consent step authenticates the user against their FitVise account (multi_user)
and issues a short-lived authorization code; the AI client then exchanges it at
/oauth/token. Tokens are stored hashed.

Hardening still to layer on (tracked, not yet wired): rate limiting, richer
consent UI, CIMD client resolution, and audience binding checks.
"""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.auth.security import hash_token, new_opaque_token, verify_password
from app.config import settings
from app.db.base import get_db, utcnow
from app.models.oauth import OAuthClient, OAuthGrant, OAuthToken
from app.models.user import User

router = APIRouter(tags=["oauth"])

CODE_TTL = 600  # 10 minutes


def _require_multi_user() -> None:
    if not settings.is_multi_user:
        raise HTTPException(404, "OAuth is disabled in single_user mode")


# ---- Dynamic Client Registration (RFC 7591) ------------------------
@router.post("/oauth/register")
def register_client(payload: dict, db: Session = Depends(get_db)) -> JSONResponse:
    _require_multi_user()
    redirect_uris = payload.get("redirect_uris") or []
    if not isinstance(redirect_uris, list) or not redirect_uris:
        raise HTTPException(400, "redirect_uris is required")

    client_id = "fv_" + secrets.token_urlsafe(16)
    client = OAuthClient(
        client_id=client_id,
        client_name=payload.get("client_name"),
        registration_type="dcr",
        redirect_uris=redirect_uris,
    )
    db.add(client)
    db.commit()
    return JSONResponse(
        status_code=201,
        content={
            "client_id": client_id,
            "client_id_issued_at": int(utcnow().timestamp()),
            "redirect_uris": redirect_uris,
            "token_endpoint_auth_method": "none",
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
        },
    )


# ---- Authorization endpoint (PKCE S256) ----------------------------
def _consent_page(params: dict, error: str | None = None) -> str:
    hidden = "".join(
        f'<input type="hidden" name="{k}" value="{v}">' for k, v in params.items() if v
    )
    err = f'<p style="color:#c2410c">{error}</p>' if error else ""
    return f"""<!doctype html><html><head><meta charset=utf-8>
<title>Authorize FitVise</title><meta name=viewport content="width=device-width,initial-scale=1">
<style>body{{font-family:system-ui;background:#f6f3ec;color:#221d18;display:flex;
justify-content:center;padding:40px}}form{{background:#fffdf9;border:1px solid #e7e1d6;
border-radius:16px;padding:24px;max-width:360px;width:100%}}input[type=email],
input[type=password]{{width:100%;padding:10px;margin:6px 0;border:1px solid #e7e1d6;
border-radius:8px}}button{{width:100%;padding:12px;background:#c2410c;color:#fff;border:0;
border-radius:8px;font-weight:600;margin-top:10px;cursor:pointer}}</style></head>
<body><form method=post action="/oauth/authorize">
<h2>Connect your AI client to FitVise</h2>
<p>Sign in to authorize access to your data.</p>{err}
<input type=email name=email placeholder=Email required>
<input type=password name=password placeholder=Password required>
{hidden}<button type=submit>Authorize</button></form></body></html>"""


@router.get("/oauth/authorize", response_class=HTMLResponse)
def authorize_get(request: Request) -> HTMLResponse:
    _require_multi_user()
    p = dict(request.query_params)
    if p.get("response_type") != "code":
        raise HTTPException(400, "Only response_type=code is supported")
    if p.get("code_challenge_method") != "S256":
        raise HTTPException(400, "PKCE with code_challenge_method=S256 is required")
    if not p.get("code_challenge"):
        raise HTTPException(400, "code_challenge is required")
    return HTMLResponse(_consent_page(p))


@router.post("/oauth/authorize")
def authorize_post(
    request: Request,
    db: Session = Depends(get_db),
    email: str = Form(...),
    password: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    code_challenge: str = Form(...),
    code_challenge_method: str = Form(...),
    response_type: str = Form("code"),
    scope: str = Form("fitvise.read fitvise.write"),
    state: str | None = Form(None),
):
    _require_multi_user()
    client = db.query(OAuthClient).filter(OAuthClient.client_id == client_id).first()
    if client is None or redirect_uri not in (client.redirect_uris or []):
        raise HTTPException(400, "Unknown client or redirect_uri")

    user = db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
        "response_type": response_type,
        "scope": scope,
        "state": state,
    }
    if not user or not user.password_hash or not verify_password(password, user.password_hash):
        return HTMLResponse(_consent_page(params, "Invalid credentials"), status_code=401)

    code = new_opaque_token(24)
    grant = OAuthGrant(
        user_id=user.id,
        client_id=client_id,
        code_hash=hash_token(code),
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
        redirect_uri=redirect_uri,
        scopes=scope.split(),
        expires_at=utcnow() + dt.timedelta(seconds=CODE_TTL),
    )
    db.add(grant)
    db.commit()

    query = {"code": code}
    if state:
        query["state"] = state
    return RedirectResponse(url=f"{redirect_uri}?{urlencode(query)}", status_code=302)


# ---- Token endpoint ------------------------------------------------
def _verify_pkce(verifier: str, challenge: str) -> bool:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    expected = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return secrets.compare_digest(expected, challenge)


def _issue_tokens(db: Session, *, user_id: str, client_id: str, scopes: list[str],
                  grant_id: str | None, rotated_from: str | None = None) -> dict:
    access = new_opaque_token(32)
    refresh = new_opaque_token(32)
    token = OAuthToken(
        grant_id=grant_id,
        user_id=user_id,
        client_id=client_id,
        access_token_hash=hash_token(access),
        refresh_token_hash=hash_token(refresh),
        scopes=scopes,
        expires_at=utcnow() + dt.timedelta(seconds=settings.oauth_access_token_ttl),
        rotated_from=rotated_from,
    )
    db.add(token)
    db.commit()
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "Bearer",
        "expires_in": settings.oauth_access_token_ttl,
        "scope": " ".join(scopes),
    }


@router.post("/oauth/token")
def token(
    db: Session = Depends(get_db),
    grant_type: str = Form(...),
    code: str | None = Form(None),
    redirect_uri: str | None = Form(None),
    client_id: str | None = Form(None),
    code_verifier: str | None = Form(None),
    refresh_token: str | None = Form(None),
):
    _require_multi_user()

    if grant_type == "authorization_code":
        if not (code and code_verifier and client_id):
            raise HTTPException(400, "code, code_verifier and client_id are required")
        grant = db.query(OAuthGrant).filter(OAuthGrant.code_hash == hash_token(code)).first()
        if grant is None or grant.revoked_at is not None:
            raise HTTPException(400, "invalid_grant")
        if grant.expires_at and grant.expires_at <= utcnow():
            raise HTTPException(400, "expired_grant")
        if grant.client_id != client_id or grant.redirect_uri != redirect_uri:
            raise HTTPException(400, "client/redirect mismatch")
        if not _verify_pkce(code_verifier, grant.code_challenge or ""):
            raise HTTPException(400, "invalid PKCE verifier")
        # one-time use: revoke the code
        grant.revoked_at = utcnow()
        db.commit()
        return _issue_tokens(
            db, user_id=grant.user_id, client_id=client_id, scopes=grant.scopes, grant_id=grant.id
        )

    if grant_type == "refresh_token":
        if not refresh_token:
            raise HTTPException(400, "refresh_token is required")
        old = (
            db.query(OAuthToken)
            .filter(OAuthToken.refresh_token_hash == hash_token(refresh_token))
            .first()
        )
        if old is None or old.revoked_at is not None:
            raise HTTPException(400, "invalid_grant")
        # rotation: revoke the old token, issue a fresh pair (PRD §3.6)
        old.revoked_at = utcnow()
        db.commit()
        return _issue_tokens(
            db,
            user_id=old.user_id,
            client_id=old.client_id,
            scopes=old.scopes,
            grant_id=old.grant_id,
            rotated_from=old.id,
        )

    raise HTTPException(400, "unsupported_grant_type")


# ---- Revocation (RFC 7009) -----------------------------------------
@router.post("/oauth/revoke")
def revoke(db: Session = Depends(get_db), token: str = Form(...)) -> JSONResponse:
    _require_multi_user()
    th = hash_token(token)
    rec = (
        db.query(OAuthToken)
        .filter(
            (OAuthToken.access_token_hash == th) | (OAuthToken.refresh_token_hash == th)
        )
        .first()
    )
    if rec and rec.revoked_at is None:
        rec.revoked_at = utcnow()
        db.commit()
    # RFC 7009 — always 200 regardless of whether the token was found.
    return JSONResponse({"ok": True})
