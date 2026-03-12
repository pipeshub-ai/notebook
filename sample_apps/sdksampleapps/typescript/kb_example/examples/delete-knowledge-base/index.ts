/**
 * Example: Delete a knowledge base by id.
 * Run from repo root: npm run run:delete  OR  npm run run:delete -- <kbId>
 * If no id is given, creates a new KB and deletes it (demo only).
 */

import { getClient } from "../../src/client";
import { deleteKnowledgeBase } from "../../src/kb-ops";
import { getKbIdOrCreate } from "../../src/resolve-kb-id";
import { logger } from "../../src/logger";

async function main(): Promise<void> {
  const client = getClient();
  const kbId = await getKbIdOrCreate(client);
  await deleteKnowledgeBase(client, kbId);
}

main().catch((err) => {
  logger.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
});
