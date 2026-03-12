# Get Knowledge Hub Child Nodes

## Overview

Fetches the child nodes of a knowledge base in the hub via `pipeshub.knowledgeBases.getKnowledgeHubChildNodes({ parentType: "kb", parentId: kbId })`. Creates a KB first to get an id, then fetches its child nodes.

## How to run

From the `kb_example` directory:

```bash
npm run run:child-nodes
```

Or directly:

```bash
npx ts-node examples/get-hub-child-nodes/index.ts
```

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `PIPESHUB_BEARER_AUTH` | Yes | Bearer token for API authentication |
| `PIPESHUB_SERVER_URL`  | No  | API base URL (default: `https://app.pipeshub.com/api/v1`) |

## Code reference

- **KB id:** Creates a KB via `createKnowledgeBase(client)` in this folder’s `index.ts`, then uses its id
- **Operation:** `getKnowledgeHubChildNodes(client, kbId)` in this folder’s `index.ts`
- **API:** `client.knowledgeBases.getKnowledgeHubChildNodes({ parentType, parentId })`
