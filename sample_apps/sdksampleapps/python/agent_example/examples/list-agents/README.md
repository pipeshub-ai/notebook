# List Agents

## Overview

Lists all agents available to the authenticated user by calling the API directly (GET /agents). Uses the same fallback as the full flow because the SDK may expect a list while the API returns a wrapped object.

## How to run

From the `agent_example` directory:

```bash
python examples/list-agents/index.py
```

Or run this example via the main entry: `python main.py list-agents`

## What you'll see

A log line followed by a JSON list of your agents (or an empty list `[]`).

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `PIPESHUB_BEARER_AUTH` | Yes (or OAuth) | Bearer token for API authentication |
| `PIPESHUB_SERVER_URL`  | No | API base URL (default: `https://app.pipeshub.com/api/v1`) |

To use OAuth instead of a bearer token, set `PIPESHUB_OAUTH_CLIENT_ID` and `PIPESHUB_OAUTH_CLIENT_SECRET` (see [auth](../auth/) example).

## Code reference

All of the following are defined in this example's `index.py` (auth is inlined; this example uses raw HTTP, not the SDK client):

- **Auth:** `get_bearer_token(server_url)` — Bearer from env or OAuth browser flow
- **Operation:** `list_agents_via_api(server_url, token)` — GET /agents and normalize response
- **API:** `GET /agents`
