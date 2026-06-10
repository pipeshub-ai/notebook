# PipesHub Knowledge Bases API — TypeScript Sample

This sample demonstrates the **Knowledge Bases** API using the PipesHub TypeScript SDK (`@pipeshub-ai/sdk`). The code is organized into small, runnable examples so you can read and run one operation at a time.

## Prerequisites

- **Node.js** 18 or later
- A PipesHub **bearer token** (e.g. from your PipesHub app or OAuth)

## Setup

1. Install dependencies:

   ```bash
   npm install
   ```

2. Configure environment:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set:

   - **`PIPESHUB_BEARER_AUTH`** (required) — your bearer token
   - **`PIPESHUB_SERVER_URL`** (optional) — API base URL; default is `https://app.pipeshub.com/api/v1`

## Running the sample

### Full flow

Runs the complete sequence: create → list → get → update → root-nodes → child-nodes → delete.

```bash
npm run dev
```

To build and run the compiled script:

```bash
npm run build && npm start
```

### Individual examples

Each example is in its own folder under `examples/` with a runnable script and a README. Use the npm scripts below, or run the script directly (see the example’s README for details).

| Example | Script | Description |
|--------|--------|-------------|
| [create-knowledge-base](examples/create-knowledge-base/) | `npm run run:create` | Create a new knowledge base |
| [list-knowledge-bases](examples/list-knowledge-bases/) | `npm run run:list` | List knowledge bases |
| [get-knowledge-base](examples/get-knowledge-base/) | `npm run run:get` | Create a KB, then get it by id |
| [update-knowledge-base](examples/update-knowledge-base/) | `npm run run:update` | Create a KB, then update it |
| [get-hub-root-nodes](examples/get-hub-root-nodes/) | `npm run run:root-nodes` | Get hub root nodes |
| [get-hub-child-nodes](examples/get-hub-child-nodes/) | `npm run run:child-nodes` | Create a KB, then get its child nodes |
| [delete-knowledge-base](examples/delete-knowledge-base/) | `npm run run:delete` | Create a KB, then delete it |

Examples that need a KB id create a knowledge base first to get the id, then run the operation.

## Project structure

| Path | Purpose |
|------|---------|
| `src/logger.ts` | Shared logger (info, warn, error, json) |
| `src/index.ts` | Full-flow entrypoint (create → … → delete); client and KB ops inlined here |
| `examples/*/` | One folder per operation: `index.ts` (runnable, with getClient + op inlined) + `README.md` |

## See also

- [PipesHub API — Knowledge Bases](https://docs.pipeshub.com/api-reference)
- Other samples in `sample_apps/sdksampleapps/` (Go, Python)
