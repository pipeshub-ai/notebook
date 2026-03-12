/**
 * Example: Get child nodes of a knowledge base in the hub.
 * Run from repo root: npm run run:child-nodes  OR  npm run run:child-nodes -- <kbId>
 * If no id is given, creates a new KB and fetches its child nodes.
 */

import { getClient } from "../../src/client";
import { getKnowledgeHubChildNodes } from "../../src/kb-ops";
import { getKbIdOrCreate } from "../../src/resolve-kb-id";
import { logger } from "../../src/logger";

async function main(): Promise<void> {
  const client = getClient();
  const kbId = await getKbIdOrCreate(client);
  await getKnowledgeHubChildNodes(client, kbId);
}

main().catch((err) => {
  logger.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
});
