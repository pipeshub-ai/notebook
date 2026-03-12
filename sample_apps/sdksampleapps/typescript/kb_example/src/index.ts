/**
 * Full Knowledge Base demo: create → list → get → update → root-nodes → child-nodes → delete.
 *
 * For a single operation, run the corresponding script under `examples/`
 * (e.g. `npm run run:create` or `npm run run:list`).
 */

import { getClient } from "./client";
import {
  createKnowledgeBase,
  listKnowledgeBases,
  getKnowledgeBase,
  updateKnowledgeBase,
  getKnowledgeHubRootNodes,
  getKnowledgeHubChildNodes,
  deleteKnowledgeBase,
} from "./kb-ops";
import { logger } from "./logger";

async function main(): Promise<void> {
  const client = getClient();

  const kbId = await createKnowledgeBase(client);
  await listKnowledgeBases(client);
  await getKnowledgeBase(client, kbId);
  await updateKnowledgeBase(client, kbId);
  await getKnowledgeHubRootNodes(client);
  await getKnowledgeHubChildNodes(client, kbId);
  await deleteKnowledgeBase(client, kbId);

  logger.info("Full flow completed successfully.");
}

main().catch((err) => {
  const message = err instanceof Error ? err.message : String(err);
  logger.error(message);
  process.exit(1);
});
