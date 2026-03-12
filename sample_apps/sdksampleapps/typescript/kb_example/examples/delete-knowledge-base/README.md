# Delete Knowledge Base

## Overview

Deletes a knowledge base by id via `pipeshub.knowledgeBases.deleteKnowledgeBase({ kbId })`. If no id is provided, creates a new KB and deletes it (for demo only).

## How to run

From the `kb_example` directory:

```bash
# No id: creates a new KB and deletes it
npm run run:delete

# With id: delete existing KB
KB_ID=your-kb-id npm run run:delete
npm run run:delete -- your-kb-id
```

Or directly:

```bash
npx ts-node examples/delete-knowledge-base/index.ts
npx ts-node examples/delete-knowledge-base/index.ts your-kb-id
```

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `PIPESHUB_BEARER_AUTH` | Yes | Bearer token for API authentication |
| `PIPESHUB_SERVER_URL`  | No  | API base URL (default: `https://app.pipeshub.com/api/v1`) |
| `KB_ID`               | No  | Knowledge base id (if omitted, a new KB is created and then deleted) |

## Code reference

- **KB id (or create):** `getKbIdOrCreate(client)` in `src/resolve-kb-id.ts`
- **Operation:** `deleteKnowledgeBase(client, kbId)` in `src/kb-ops.ts`
- **API:** `client.knowledgeBases.deleteKnowledgeBase({ kbId })`
