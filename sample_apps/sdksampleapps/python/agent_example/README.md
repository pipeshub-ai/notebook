# PipesHub Agents API — Python Sample

This sample demonstrates the **Agents** API using the PipesHub Python SDK (`pipeshub-sdk`). The code is organized into small, runnable examples so you can read and run one operation at a time.

## Prerequisites

- **Python** 3.10 or later
- A PipesHub **bearer token** or **OAuth app** (client ID + secret) for browser login

## Setup

1. Install dependencies:

   ```bash
   pip install -e .
   ```

   Or with uv:

   ```bash
   uv pip install -e .
   ```

2. Configure environment:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set:

   - **`PIPESHUB_BEARER_AUTH`** (optional if using OAuth) — your bearer token
   - **`PIPESHUB_OAUTH_CLIENT_ID`** and **`PIPESHUB_OAUTH_CLIENT_SECRET`** — for OAuth browser login (create an OAuth app in PipesHub; redirect URI: `http://localhost:8765/callback`)
   - **`PIPESHUB_SERVER_URL`** (optional) — API base URL; default is `https://app.pipeshub.com/api/v1`

## Running the sample

### Main entry (run one or all examples)

`main.py` is the main entrypoint. Run all examples in sequence, or a single example by name (from the `agent_example` directory):

```bash
# Run all examples in order: auth → list-agents → create-agent → chat-with-agent
python main.py

# Run a single example
python main.py auth
python main.py list-agents
python main.py create-agent
python main.py chat-with-agent
```

After `pip install -e .` you can also run:

```bash
agent-example
agent-example auth
agent-example list-agents
# etc.
```

### Full flow (single script)

To run the complete sequence in one go (authenticate → create new agent → interactive chat REPL) without switching examples:

```bash
python src/index.py
```

### Individual examples (run separately)

Each example can also be run directly. From the `agent_example` directory:

| Example | Command | Description |
|--------|--------|-------------|
| [auth](examples/auth/) | `python examples/auth/index.py` | Get bearer token (env or OAuth browser login) |
| [list-agents](examples/list-agents/) | `python examples/list-agents/index.py` | List agents for the user |
| [create-agent](examples/create-agent/) | `python examples/create-agent/index.py` | Create a new SDK Demo Agent (no reuse) |
| [chat-with-agent](examples/chat-with-agent/) | `python examples/chat-with-agent/index.py` | Interactive chat with the agent (REPL) |

## Project structure

| Path | Purpose |
|------|---------|
| `main.py` | Main entrypoint: run all examples or one by name (auth, list-agents, create-agent, chat-with-agent) |
| `src/auth.py` | Shared auth: get bearer token from env or OAuth browser login (PKCE) |
| `src/logger.py` | Shared logger (info, warn, error, json) |
| `src/index.py` | Full flow in one go (auth → create agent → chat REPL) |
| `examples/*/` | One folder per operation: `index.py` (runnable) + `README.md` |

## See also

- [PipesHub API — Agents](https://docs.pipeshub.com/api-reference)
- Other samples in `sample_apps/sdksampleapps/` (TypeScript, Go)
