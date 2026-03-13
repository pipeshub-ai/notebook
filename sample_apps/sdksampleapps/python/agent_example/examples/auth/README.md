# Auth (Get Bearer Token)

## Overview

Obtains a PipesHub bearer token either from the environment (`PIPESHUB_BEARER_AUTH`) or via **OAuth browser login**: a login link opens in your browser, you sign in to PipesHub, and the sample receives the token on a local callback (PKCE flow). Logs a short token preview on success.

## How to run

From the `agent_example` directory:

```bash
python examples/auth/index.py
```

Or run this example via the main entry: `python main.py auth`

## What you'll see

If `PIPESHUB_BEARER_AUTH` is set: a log line with a short token prefix (e.g. `Got bearer token abc...`) and no browser. If using OAuth: your browser opens for PipesHub login, then a "Login successful! You can close this tab." page.

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `PIPESHUB_BEARER_AUTH` | No (if using OAuth) | Bearer token for API authentication |
| `PIPESHUB_SERVER_URL`  | No | API base URL (default: `https://app.pipeshub.com/api/v1`) |
| `PIPESHUB_OAUTH_CLIENT_ID` | Yes (if not using bearer token) | OAuth client ID from your PipesHub OAuth app |
| `PIPESHUB_OAUTH_CLIENT_SECRET` | Yes (if not using bearer token) | OAuth client secret |
| `PIPESHUB_OAUTH_REDIRECT_PORT` | No | Local port for OAuth callback (default: 8765) |

**OAuth app setup:** In PipesHub, create an OAuth application and set the redirect URI to `http://localhost:8765/callback` (or the port you use). Use the app’s client ID and secret in `.env`.

## Code reference

- **Token helper:** `get_bearer_token(server_url)` is defined in this example (no shared auth module).
- **API:** `GET /oauth2/authorize`, `POST /oauth2/token` (OAuth 2.0 with PKCE)
