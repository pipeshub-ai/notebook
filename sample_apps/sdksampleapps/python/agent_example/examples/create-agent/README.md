# Create Agent

## Overview

Creates a new **SDK Demo Agent** every time (does not reuse existing by name). Uses the first available LLM/reasoning models (preferring GPT-4o). Prints the agent key.

## How to run

From the `agent_example` directory:

```bash
python examples/create-agent/index.py
```

Or run this example via the main entry: `python main.py create-agent`

## What you'll see

Log lines with the agent name and the created agent key. The key is also printed at the end (use it for chat or API calls).

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `PIPESHUB_BEARER_AUTH` | Yes (or OAuth) | Bearer token for API authentication |
| `PIPESHUB_SERVER_URL`  | No | API base URL (default: `https://app.pipeshub.com/api/v1`) |

To use OAuth instead of a bearer token, set `PIPESHUB_OAUTH_CLIENT_ID` and `PIPESHUB_OAUTH_CLIENT_SECRET` (see [auth](../auth/) example).

## Code reference

- **Client:** `get_bearer_token`, `get_pipeshub_client` (in-file)
- **Operation:** `create_agent(pipeshub, server_url, token)` in `index.py`
- **API:** `POST /agents/create`
