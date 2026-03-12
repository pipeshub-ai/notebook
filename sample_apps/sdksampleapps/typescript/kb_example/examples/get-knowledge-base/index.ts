/**
 * Example: Get a single knowledge base by id.
 * Run from repo root: npm run run:get  OR  npm run run:get -- <kbId>
 * If no id is given, creates a new KB and fetches it.
 */

import { getClient } from "../../src/client";
import { getKnowledgeBase } from "../../src/kb-ops";
import { getKbIdOrCreate } from "../../src/resolve-kb-id";
import { logger } from "../../src/logger";

async function main(): Promise<void> {
  const client = getClient();
  const kbId = await getKbIdOrCreate(client);
  await getKnowledgeBase(client, kbId);
}

main().catch((err) => {
  logger.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
});
