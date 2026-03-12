# Get Knowledge Base

## Overview

Fetches a single knowledge base by ID via `pipeshub.knowledgeBases.getKnowledgeBase({ kbId })`. If no id is provided, creates a new KB and fetches it.

## How to run

From the `kb_example` directory:

```bash
# No id: creates a new KB and gets it
npm run run:get

# With id: use existing KB (env or first argument)
KB_ID=your-kb-id npm run run:get
npm run run:get -- your-kb-id
```

Or directly:

```bash
npx ts-node examples/get-knowledge-base/index.ts
npx ts-node examples/get-knowledge-base/index.ts your-kb-id
```

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `PIPESHUB_BEARER_AUTH` | Yes | Bearer token for API authentication |
| `PIPESHUB_SERVER_URL`  | No  | API base URL (default: `https://app.pipeshub.com/api/v1`) |
| `KB_ID`               | No  | Knowledge base id (if omitted, a new KB is created and used) |

## Code reference

- **KB id (or create):** `getKbIdOrCreate(client)` in `src/resolve-kb-id.ts`
- **Operation:** `getKnowledgeBase(client, kbId)` in `src/kb-ops.ts`
- **API:** `client.knowledgeBases.getKnowledgeBase({ kbId })`
