# Create Knowledge Base

## Overview

Creates a new knowledge base via the PipesHub API. The call `pipeshub.knowledgeBases.createKnowledgeBase({ kbName })` returns the new KB metadata, including its `id`.

## How to run

From the `kb_example` directory:

```bash
npm run run:create
```

Or directly:

```bash
npx ts-node examples/create-knowledge-base/index.ts
```

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `PIPESHUB_BEARER_AUTH` | Yes | Bearer token for API authentication |
| `PIPESHUB_SERVER_URL`  | No  | API base URL (default: `https://app.pipeshub.com/api/v1`) |

## Code reference

- **Client:** `getClient()` in `src/client.ts`
- **Operation:** `createKnowledgeBase(client)` in `src/kb-ops.ts`
- **API:** `client.knowledgeBases.createKnowledgeBase({ kbName })`
