# Get Knowledge Hub Child Nodes

## Overview

Fetches the child nodes of a knowledge base in the hub via `pipeshub.knowledgeBases.getKnowledgeHubChildNodes({ parentType: "kb", parentId: kbId })`. If no id is provided, creates a new KB and fetches its child nodes.

## How to run

From the `kb_example` directory:

```bash
# No id: creates a new KB and gets its child nodes
npm run run:child-nodes

# With id: use existing KB
KB_ID=your-kb-id npm run run:child-nodes
npm run run:child-nodes -- your-kb-id
```

Or directly:

```bash
npx ts-node examples/get-hub-child-nodes/index.ts
npx ts-node examples/get-hub-child-nodes/index.ts your-kb-id
```

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `PIPESHUB_BEARER_AUTH` | Yes | Bearer token for API authentication |
| `PIPESHUB_SERVER_URL`  | No  | API base URL (default: `https://app.pipeshub.com/api/v1`) |
| `KB_ID`               | No  | Knowledge base id (if omitted, a new KB is created and used) |

## Code reference

- **KB id (or create):** `getKbIdOrCreate(client)` in `src/resolve-kb-id.ts`
- **Operation:** `getKnowledgeHubChildNodes(client, kbId)` in `src/kb-ops.ts`
- **API:** `client.knowledgeBases.getKnowledgeHubChildNodes({ parentType, parentId })`
