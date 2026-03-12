# Get Knowledge Hub Root Nodes

## Overview

Fetches the root nodes of the knowledge hub (top-level knowledge bases, connectors, and apps) via `pipeshub.knowledgeBases.getKnowledgeHubRootNodes({})`.

## How to run

From the `kb_example` directory:

```bash
npm run run:root-nodes
```

Or directly:

```bash
npx ts-node examples/get-hub-root-nodes/index.ts
```

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `PIPESHUB_BEARER_AUTH` | Yes | Bearer token for API authentication |
| `PIPESHUB_SERVER_URL`  | No  | API base URL (default: `https://app.pipeshub.com/api/v1`) |

## Code reference

- **Client:** `getClient()` in this folder’s `index.ts`
- **Operation:** `getKnowledgeHubRootNodes(client)` in this folder’s `index.ts`
- **API:** `client.knowledgeBases.getKnowledgeHubRootNodes({})`
