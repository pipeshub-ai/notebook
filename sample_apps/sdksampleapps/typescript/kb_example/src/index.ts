/**
 * Full Knowledge Base demo: runs the complete flow in order.
 *
 * Flow: create → list → get → update → root-nodes → child-nodes → delete.
 *
 * To run a single operation instead, use the script under examples/
 * (e.g. npm run run:create or npm run run:list).
 *
 * Run: npm run dev   OR   npm run build && npm start
 */

import "dotenv/config";
import { Pipeshub } from "@pipeshub-ai/sdk";
import { logger } from "./logger";

// --- Configuration ---

/** Display name for newly created knowledge bases. */
const DEFAULT_KB_NAME = "Sample KB - TypeScript Demo";
/** Name applied when we update a KB in this demo. */
const UPDATED_KB_NAME = "Updated - TypeScript Demo";
/** PipesHub API base URL when not overridden by env. */
const DEFAULT_SERVER_URL = "https://app.pipeshub.com/api/v1";

/** Environment variable names used by this sample. */
const ENV = {
  BEARER_AUTH: "PIPESHUB_BEARER_AUTH",
  SERVER_URL: "PIPESHUB_SERVER_URL",
} as const;

// --- Client ---

/**
 * Builds and returns a configured PipesHub client.
 * Reads PIPESHUB_BEARER_AUTH from env (required). Optionally PIPESHUB_SERVER_URL.
 */
function getClient(): Pipeshub {
  const bearerAuth = process.env[ENV.BEARER_AUTH];
  if (!bearerAuth?.trim()) {
    logger.error(
      `Missing required environment variable: ${ENV.BEARER_AUTH}. Set it in .env or your shell.`
    );
    throw new Error(`Required: ${ENV.BEARER_AUTH}`);
  }
  const serverUrl = process.env[ENV.SERVER_URL]?.trim() || DEFAULT_SERVER_URL;
  return new Pipeshub({
    security: { bearerAuth: bearerAuth.trim() },
    serverURL: serverUrl,
  });
}

// --- Knowledge Base operations ---

/** Creates a new knowledge base and returns its id. */
async function createKnowledgeBase(pipeshub: Pipeshub): Promise<string> {
  logger.info("Creating knowledge base...");
  const response = await pipeshub.knowledgeBases.createKnowledgeBase({
    kbName: DEFAULT_KB_NAME,
  });
  const kbId = response.id ?? "";
  if (!kbId) {
    throw new Error("Create response did not include an id");
  }
  logger.json("Created knowledge base", response);
  return kbId;
}

/** Lists knowledge bases for the authenticated user (owner/organizer/writer, limit 10). */
async function listKnowledgeBases(pipeshub: Pipeshub): Promise<void> {
  logger.info("Listing knowledge bases...");
  const response = await pipeshub.knowledgeBases.listKnowledgeBases({
    permissions: "OWNER,ORGANIZER,WRITER",
    limit: 10,
    sortBy: "createdAtTimestamp",
  });
  logger.json("Knowledge bases", response);
}

/** Fetches a single knowledge base by id and logs it. */
async function getKnowledgeBase(
  pipeshub: Pipeshub,
  kbId: string
): Promise<void> {
  logger.info("Fetching knowledge base", { kbId });
  const response = await pipeshub.knowledgeBases.getKnowledgeBase({
    kbId,
  });
  logger.json("Knowledge base", response);
}

/** Updates a knowledge base (e.g. name) and logs the result. */
async function updateKnowledgeBase(
  pipeshub: Pipeshub,
  kbId: string
): Promise<void> {
  logger.info("Updating knowledge base", { kbId, newName: UPDATED_KB_NAME });
  await pipeshub.knowledgeBases.updateKnowledgeBase({
    kbId,
    body: { kbName: UPDATED_KB_NAME },
  });
  const updated = await pipeshub.knowledgeBases.getKnowledgeBase({ kbId });
  logger.json("Knowledge base after update", updated);
}

/** Fetches the root nodes of the knowledge hub (top-level KBs, connectors, apps). */
async function getKnowledgeHubRootNodes(pipeshub: Pipeshub): Promise<void> {
  logger.info("Fetching knowledge hub root nodes...");
  const response =
    await pipeshub.knowledgeBases.getKnowledgeHubRootNodes({});
  logger.json("Root nodes", response);
}

/** Fetches the child nodes of a knowledge base in the hub. */
async function getKnowledgeHubChildNodes(
  pipeshub: Pipeshub,
  kbId: string
): Promise<void> {
  logger.info("Fetching child nodes for knowledge base", { kbId });
  const response =
    await pipeshub.knowledgeBases.getKnowledgeHubChildNodes({
      parentType: "kb",
      parentId: kbId,
    });
  logger.json("Child nodes", response);
}

/** Deletes a knowledge base by id. */
async function deleteKnowledgeBase(
  pipeshub: Pipeshub,
  kbId: string
): Promise<void> {
  logger.info("Deleting knowledge base", { kbId });
  await pipeshub.knowledgeBases.deleteKnowledgeBase({ kbId });
  logger.info("Knowledge base deleted successfully.");
}

// --- Entry point ---

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
