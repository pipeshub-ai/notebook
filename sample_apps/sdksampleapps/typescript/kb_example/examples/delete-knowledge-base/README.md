# Delete Knowledge Base

## Overview

Deletes a knowledge base by id via `pipeshub.knowledgeBases.deleteKnowledgeBase({ kbId })`. Creates a KB first to get an id, then deletes it.

## How to run

From the `kb_example` directory:

```bash
npm run run:delete
```

Or directly:

```bash
npx ts-node examples/delete-knowledge-base/index.ts
```

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `PIPESHUB_BEARER_AUTH` | Yes | Bearer token for API authentication |
| `PIPESHUB_SERVER_URL`  | No  | API base URL (default: `https://app.pipeshub.com/api/v1`) |

## Code reference

- **KB id:** Creates a KB via `createKnowledgeBase(client)` in this folder’s `index.ts`, then uses its id
- **Operation:** `deleteKnowledgeBase(client, kbId)` in this folder’s `index.ts`
- **API:** `client.knowledgeBases.deleteKnowledgeBase({ kbId })`
