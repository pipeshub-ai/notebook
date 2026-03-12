# List Knowledge Bases

## Overview

Lists knowledge bases available to the authenticated user. Uses `pipeshub.knowledgeBases.listKnowledgeBases()` with optional filters (permissions, limit, sort order).

## How to run

From the `kb_example` directory:

```bash
npm run run:list
```

Or directly:

```bash
npx ts-node examples/list-knowledge-bases/index.ts
```

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `PIPESHUB_BEARER_AUTH` | Yes | Bearer token for API authentication |
| `PIPESHUB_SERVER_URL`  | No  | API base URL (default: `https://app.pipeshub.com/api/v1`) |

## Code reference

- **Client:** `getClient()` in `src/client.ts`
- **Operation:** `listKnowledgeBases(client)` in `src/kb-ops.ts`
- **API:** `client.knowledgeBases.listKnowledgeBases({ permissions, limit, sortBy })`
