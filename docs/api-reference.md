# FitVise REST API reference

Base path: `/api/v1`. Interactive docs (OpenAPI/Swagger) at `/docs`, schema at
`/openapi.json`.

## Authentication

- **single_user:** no token required; all requests resolve to the sole user.
- **multi_user / managed:** send `Authorization: Bearer <app-JWT>` obtained from
  `/api/v1/auth/login` or `/register`. (The MCP path uses OAuth tokens, separate
  from this app JWT.)

All endpoints require auth except `/health` and the OAuth discovery documents.

## Conventions

- Timestamps are ISO 8601 with timezone.
- List endpoints accept `start_date` / `end_date` (`YYYY-MM-DD`) query filters.
- Deletes are **soft** (`deleted_at`); data is never hard-deleted without intent.

---

## Endpoints

### Health & meta
| Method | Path | Notes |
|---|---|---|
| GET | `/health` | version, DB, MCP, OAuth, webpush status |
| GET | `/` | service summary + MCP endpoint |

### Auth
| Method | Path | Body |
|---|---|---|
| POST | `/api/v1/auth/register` | `{name,email,password}` → token (multi_user) |
| POST | `/api/v1/auth/login` | `{email,password}` → token (multi_user) |
| GET | `/api/v1/auth/me` | current user |

### Profile / onboarding
| Method | Path |
|---|---|
| GET / PUT | `/api/v1/profile` |
| PATCH | `/api/v1/profile/user` |
| GET | `/api/v1/profile/onboarding-status` |
| POST | `/api/v1/profile/complete-onboarding` |

### Programme
| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/programme/current` | active programme + this week's sessions |
| GET | `/api/v1/programme/history` | all versions (audit trail) |
| PUT | `/api/v1/programme` | validated write; archives prior, notifies user |

### Logging
| Method | Path |
|---|---|
| GET / POST | `/api/v1/workouts` · DELETE `/{id}` |
| GET / POST | `/api/v1/diet` · DELETE `/{id}` |
| GET / POST | `/api/v1/metrics` · DELETE `/{id}` |
| GET / POST | `/api/v1/recovery` · DELETE `/{id}` |
| GET / POST | `/api/v1/journal/flags` |
| GET / POST | `/api/v1/journal/injuries` |
| GET / POST | `/api/v1/journal/victories` |

### Check-ins & targets
| Method | Path |
|---|---|
| GET / POST | `/api/v1/checkins` |
| GET / POST | `/api/v1/checkins/targets` |

### Notifications
| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/notifications` | `?unread_only=true` |
| GET | `/api/v1/notifications/unread-count` | |
| POST | `/api/v1/notifications/{id}/read` | |
| POST | `/api/v1/notifications/read-all` | |
| GET / PUT | `/api/v1/notifications/preferences` | channels + reminder time |
| GET | `/api/v1/notifications/vapid-public-key` | for Web Push subscribe |
| POST | `/api/v1/notifications/push/subscribe` | `{endpoint,keys:{p256dh,auth}}` |
| POST | `/api/v1/notifications/push/unsubscribe` | `?endpoint=` |
| POST | `/api/v1/notifications/test` | send a test notification |

### Export
| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/export/json` | full-fidelity JSON |
| GET | `/api/v1/export/csv` | zip, one CSV per entity |

---

## OAuth 2.1 (multi_user / managed)

| Method | Path | Notes |
|---|---|---|
| GET | `/.well-known/oauth-protected-resource` | RFC 9728 |
| GET | `/.well-known/oauth-authorization-server` | RFC 8414, advertises `S256` |
| POST | `/oauth/register` | Dynamic Client Registration (RFC 7591) |
| GET/POST | `/oauth/authorize` | auth-code flow, PKCE `S256`, consent + login |
| POST | `/oauth/token` | `authorization_code` + `refresh_token` (rotated) |
| POST | `/oauth/revoke` | RFC 7009 |

## MCP

Single endpoint `POST/GET /mcp` (Streamable HTTP). See
[mcp-setup.md](mcp-setup.md) for the tool/prompt catalogue and connection flow.

### MCP response envelope

```json
{ "success": true, "data": { }, "meta": { "user_id": "…", "fetched_at": "…", "context_note": "…" } }
```
```json
{ "success": false, "error": "…", "code": "NOT_FOUND | UNAUTHORIZED | INVALID_PARAMS | VALIDATION_FAILED" }
```
