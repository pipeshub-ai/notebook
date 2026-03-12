# PipesHub KnowledgeBases API – TypeScript Sample

This sample demonstrates the **KnowledgeBases** API using the PipesHub TypeScript SDK (`@pipeshub-ai/sdk`).

**What it does:** Runs a linear flow: create a knowledge base, list and get it, update its name, fetch knowledge hub root and child nodes, then delete the KB for cleanup. Each step logs a clear header and the API response.

## Prerequisites

- **Node.js** 18 or later
- A PipesHub **bearer token** (e.g. from your PipesHub app or OAuth)

## Setup

1. Install dependencies:

   ```bash
   npm install
   ```

2. Copy the example env file and set your token:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set `PIPESHUB_BEARER_AUTH` to your bearer token. Optionally set `PIPESHUB_SERVER_URL` if you use a different API base (default is `https://app.pipeshub.com/api/v1`).

## Run

- **Full flow (default):** create → list → get → update → root-nodes → child-nodes → delete

  ```bash
  npm run dev
  ```

- **Individual commands** — pass one or more commands in order. For commands that need a KB id (`get`, `update`, `child-nodes`, `delete`), pass the id as the next argument or set `KB_ID` in the environment.

- **Help:** `npm run dev -- --help`

### Command reference (full examples)

| Command | Description | Example |
|--------|-------------|---------|
| `create` | Create a new knowledge base (prints id) | `npm run dev -- create` |
| `list` | List knowledge bases | `npm run dev -- list` |
| `get <kbId>` | Get a single KB by id | `npm run dev -- get 4f2426f1-251c-4ff3-941e-5571b4eb31b6` |
| `update <kbId>` | Update KB name | `npm run dev -- update 4f2426f1-251c-4ff3-941e-5571b4eb31b6` |
| `root-nodes` | Get knowledge hub root nodes | `npm run dev -- root-nodes` |
| `child-nodes <kbId>` | Get child nodes of a KB | `npm run dev -- child-nodes 4f2426f1-251c-4ff3-941e-5571b4eb31b6` |
| `delete <kbId>` | Delete a knowledge base | `npm run dev -- delete 4f2426f1-251c-4ff3-941e-5571b4eb31b6` |
| `all` | Run full flow (same as no args) | `npm run dev -- all` |

**Using `KB_ID` instead of inline id:**

```bash
export KB_ID=4f2426f1-251c-4ff3-941e-5571b4eb31b6
npm run dev -- get
npm run dev -- update
npm run dev -- child-nodes
npm run dev -- delete
```

**Chaining multiple commands:**

```bash
npm run dev -- create list
npm run dev -- list root-nodes
npm run dev -- get 4f2426f1-251c-4ff3-941e-5571b4eb31b6 update child-nodes
```

- **Build then run:** `npm run build && npm start`

## Operations demonstrated

| Step | Operation | Description |
|------|------------|-------------|
| 1 | `createKnowledgeBase` | Create a new knowledge base |
| 2 | `listKnowledgeBases` | List KBs with optional limit/sort |
| 3 | `getKnowledgeBase` | Get a single KB by ID |
| 4 | `updateKnowledgeBase` | Update the KB name |
| 5 | `getKnowledgeHubRootNodes` | Get root nodes (KBs, connectors, apps) |
| 6 | `getKnowledgeHubChildNodes` | Get children of the created KB |
| 7 | `deleteKnowledgeBase` | Delete the KB (cleanup) |

**Not exercised in this sample:**

- **`reindexFailedRecords`** – Used for connector-specific reindexing; requires a connector context.
- **`moveRecord`** – Moves a record within a KB; requires a `recordId` (e.g. from an upload or connector). Example: `moveRecord({ kbId, recordId, body: { targetFolderId: "..." } })` or an empty body to move to root.

## See also

- [PipesHub API – KnowledgeBases](https://docs.pipeshub.com/api-reference)
- Other samples in `sample_apps/sdksampleapps/` (Go, Python)
