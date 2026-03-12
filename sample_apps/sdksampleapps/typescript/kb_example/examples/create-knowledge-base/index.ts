/**
 * Example: Create a new knowledge base.
 * Run from repo root: npm run run:create  OR  npx ts-node examples/create-knowledge-base/index.ts
 */

import { getClient } from "../../src/client";
import { createKnowledgeBase } from "../../src/kb-ops";
import { logger } from "../../src/logger";

async function main(): Promise<void> {
  const client = getClient();
  const kbId = await createKnowledgeBase(client);
  logger.info("Created knowledge base id:", kbId);
}

main().catch((err) => {
  logger.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
});
