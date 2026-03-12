/**
 * Example: List knowledge bases for the authenticated user.
 * Run from repo root: npm run run:list  OR  npx ts-node examples/list-knowledge-bases/index.ts
 */

import { getClient } from "../../src/client";
import { listKnowledgeBases } from "../../src/kb-ops";
import { logger } from "../../src/logger";

async function main(): Promise<void> {
  const client = getClient();
  await listKnowledgeBases(client);
}

main().catch((err) => {
  logger.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
});
