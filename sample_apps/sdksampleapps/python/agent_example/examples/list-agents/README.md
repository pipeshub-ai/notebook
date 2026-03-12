# List Agents

## Overview

Lists all agents available to the authenticated user by calling the API directly (GET /agents). Uses the same fallback as the full flow because the SDK may expect a list while the API returns a wrapped object.

## How to run

From the `agent_example` directory:

```bash
python examples/list-agents/index.py
```

Or run this example via the main entry: `python main.py list-agents`

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `PIPESHUB_BEARER_AUTH` | Yes (or email/password) | Bearer token for API authentication |
| `PIPESHUB_SERVER_URL`  | No | API base URL (default: `https://app.pipeshub.com/api/v1`) |

## Code reference

- **Client:** `get_bearer_token`, `get_pipeshub_client` in `examples/common.py`
- **Operation:** `list_agents_via_api(server_url, token)` in `examples/common.py`
- **API:** `GET /agents`
