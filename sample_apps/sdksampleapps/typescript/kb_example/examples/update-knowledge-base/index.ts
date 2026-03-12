/**
 * Example: Update a knowledge base (e.g. name).
 * Run from repo root: npm run run:update  OR  npm run run:update -- <kbId>
 * If no id is given, creates a new KB and updates it.
 */

import { getClient } from "../../src/client";
import { updateKnowledgeBase } from "../../src/kb-ops";
import { getKbIdOrCreate } from "../../src/resolve-kb-id";
import { logger } from "../../src/logger";

async function main(): Promise<void> {
  const client = getClient();
  const kbId = await getKbIdOrCreate(client);
  await updateKnowledgeBase(client, kbId);
}

main().catch((err) => {
  logger.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
});
