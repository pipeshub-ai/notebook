# Update Knowledge Base

## Overview

Updates a knowledge base (e.g. its name) via `pipeshub.knowledgeBases.updateKnowledgeBase({ kbId, body })`, then fetches and logs the updated resource. If no id is provided, creates a new KB and updates it.

## How to run

From the `kb_example` directory:

```bash
# No id: creates a new KB and updates it
npm run run:update

# With id: use existing KB
KB_ID=your-kb-id npm run run:update
npm run run:update -- your-kb-id
```

Or directly:

```bash
npx ts-node examples/update-knowledge-base/index.ts
npx ts-node examples/update-knowledge-base/index.ts your-kb-id
```

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `PIPESHUB_BEARER_AUTH` | Yes | Bearer token for API authentication |
| `PIPESHUB_SERVER_URL`  | No  | API base URL (default: `https://app.pipeshub.com/api/v1`) |
| `KB_ID`               | No  | Knowledge base id (if omitted, a new KB is created and used) |

## Code reference

- **KB id (or create):** `getKbIdOrCreate(client)` in `src/resolve-kb-id.ts`
- **Operation:** `updateKnowledgeBase(client, kbId)` in `src/kb-ops.ts`
- **API:** `client.knowledgeBases.updateKnowledgeBase({ kbId, body: { kbName } })`
