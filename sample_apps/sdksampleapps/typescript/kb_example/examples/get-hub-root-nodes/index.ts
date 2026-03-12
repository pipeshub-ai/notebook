/**
 * Example: Get knowledge hub root nodes (top-level KBs, connectors, apps).
 * Run from repo root: npm run run:root-nodes  OR  npx ts-node examples/get-hub-root-nodes/index.ts
 */

import { getClient } from "../../src/client";
import { getKnowledgeHubRootNodes } from "../../src/kb-ops";
import { logger } from "../../src/logger";

async function main(): Promise<void> {
  const client = getClient();
  await getKnowledgeHubRootNodes(client);
}

main().catch((err) => {
  logger.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
});
