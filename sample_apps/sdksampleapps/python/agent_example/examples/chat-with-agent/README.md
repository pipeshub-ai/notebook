# Chat With Agent

## Overview

Runs the full interactive chat: creates a **new** SDK Demo Agent for this run (no reuse), then starts a REPL. You type messages and the agent replies (using the direct conversation API and optional polling). Type `quit` or `exit` to stop.

## How to run

From the `agent_example` directory:

```bash
python examples/chat-with-agent/index.py
```

Or run this example via the main entry: `python main.py chat-with-agent`

## What you'll see

A prompt `> `; you type a message and the agent replies. Type `quit` or `exit` to end the session.

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `PIPESHUB_BEARER_AUTH` | Yes (or OAuth) | Bearer token for API authentication |
| `PIPESHUB_SERVER_URL`  | No | API base URL (default: `https://app.pipeshub.com/api/v1`) |

To use OAuth instead of a bearer token, set `PIPESHUB_OAUTH_CLIENT_ID` and `PIPESHUB_OAUTH_CLIENT_SECRET` (see [auth](../auth/) example).

## Code reference

- **Client:** `get_bearer_token`, `get_pipeshub_client` (in-file)
- **Agent:** `create_agent_for_chat(pipeshub, server_url, token)` in `index.py` (creates new agent each run)
- **Chat:** `run_repl(...)` in `index.py`
- **API:** `POST /agents/{agentKey}/conversations`, `POST .../conversations/{id}/messages`, `GET .../conversations/{id}`
