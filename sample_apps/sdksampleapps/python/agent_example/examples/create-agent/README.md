# Create Agent

## Overview

Creates a new **SDK Demo Agent** every time (does not reuse existing by name). Uses the first available LLM/reasoning models (preferring GPT-4o). Prints the agent key.

## How to run

From the `agent_example` directory:

```bash
python examples/create-agent/index.py
```

Or run this example via the main entry: `python main.py create-agent`

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `PIPESHUB_BEARER_AUTH` | Yes (or email/password) | Bearer token for API authentication |
| `PIPESHUB_SERVER_URL`  | No | API base URL (default: `https://app.pipeshub.com/api/v1`) |

## Code reference

- **Client:** `get_bearer_token`, `get_pipeshub_client` (in-file)
- **Operation:** `create_agent(pipeshub, server_url, token)` in `index.py`
- **API:** `POST /agents/create`
