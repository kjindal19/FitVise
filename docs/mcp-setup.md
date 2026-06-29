# Connecting an AI client to FitVise (MCP)

FitVise exposes an **MCP server** so your AI client can act as your coach with
full context. This is the most important end-user step. The coaching
conversation happens **in your AI client** — FitVise stores and serves the data.

## What you'll need

- Your FitVise instance URL (e.g. `https://fitvise.example.com`).
- An MCP-capable AI client (Claude Desktop, claude.ai custom connectors, etc.).

The MCP endpoint is always:

```
<your-instance-url>/mcp
```

Transport is **Streamable HTTP** (the modern MCP remote transport). The legacy
HTTP+SSE transport is not used.

---

## Multi-user / managed instances (OAuth 2.1)

1. In your AI client, open connector settings and **add a custom connector**
   pointing at `https://<your-host>/mcp`.
2. The client discovers auth automatically via:
   - `/.well-known/oauth-protected-resource` (RFC 9728)
   - `/.well-known/oauth-authorization-server` (RFC 8414)
3. You'll be sent to FitVise to **sign in and authorize** (OAuth
   authorization-code flow with PKCE `S256`). No keys to copy.
4. The client stores and refreshes tokens for you. Every tool call carries your
   token; FitVise resolves it to your account and scopes all data to you.

> Static keys / tokens embedded in a URL are **not** supported by claude.ai
> remote connectors — the OAuth flow above is the supported path.

---

## Single-user self-host (stdio + static key)

For a local one-person setup, run your AI client and the FitVise MCP server on
the same machine. Use the static key from setup
(`FITVISE_MCP_API_KEY`) and a stdio connector configuration. (Remote exposure of
single-user mode can optionally require that same key via the `Authorization:
Bearer` or `x-api-key` header.)

---

## Verify the connection

In your AI client, run the onboarding slash command:

```
/mcp__fitvise__onboard
```

If your client doesn't surface MCP prompts as slash commands, the FitVise app
(Connect screen) gives you a **copy-paste starter prompt** instead — FitVise
can't inject text into your AI session, so you start the conversation there.

### Available prompts (slash commands)

| Prompt | Purpose |
|---|---|
| `/mcp__fitvise__onboard` | Capture your profile and author a first programme |
| `/mcp__fitvise__weekly_checkin` | Run the weekly check-in + set next-week targets |
| `/mcp__fitvise__change_workout` | Modify your current programme |
| `/mcp__fitvise__log_review` | Review recent logs and surface gentle patterns |

### Tools the coach can call

Reads: `get_user_profile`, `get_onboarding_status`, `get_current_programme`,
`get_session_plan`, `get_workout_logs`, `get_diet_logs`, `get_body_metrics`,
`get_recovery_logs`, `get_behaviour_flags`, `get_injury_log`,
`get_checkin_history`, `get_lift_progression`, `get_non_scale_victories`.

Writes: `update_programme` (validated; archives the prior version),
`complete_onboarding`, `write_checkin_summary`, `set_weekly_targets`,
`add_exercise_substitution`.

Write tools also trigger FitVise notifications (e.g. "your coach updated your
programme") so you're nudged in the app and via Web Push.

---

## Troubleshooting

- **401 / UNAUTHORIZED from a tool** — your token expired or wasn't sent.
  Re-authorize the connector.
- **Connector can't discover auth** — confirm `FITVISE_BASE_URL` matches the
  public URL and that `/.well-known/oauth-authorization-server` is reachable.
- **Endpoint redirects** — `/mcp` 307-redirects to `/mcp/`, preserving method;
  compliant clients follow it.
