# Update Knowledge Base

## Overview

Updates a knowledge base (e.g. its name) via `pipeshub.knowledgeBases.updateKnowledgeBase({ kbId, body })`, then fetches and logs the updated resource. Creates a KB first to get an id, then updates it.

## How to run

From the `kb_example` directory:

```bash
npm run run:update
```

Or directly:

```bash
npx ts-node examples/update-knowledge-base/index.ts
```

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `PIPESHUB_BEARER_AUTH` | Yes | Bearer token for API authentication |
| `PIPESHUB_SERVER_URL`  | No  | API base URL (default: `https://app.pipeshub.com/api/v1`) |

## Code reference

- **KB id:** Creates a KB via `createKnowledgeBase(client)` in this folder’s `index.ts`, then uses its id
- **Operation:** `updateKnowledgeBase(client, kbId)` in this folder’s `index.ts`
- **API:** `client.knowledgeBases.updateKnowledgeBase({ kbId, body: { kbName } })`
