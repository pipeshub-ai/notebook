/**
 * Example: Update a knowledge base (e.g. its name).
 *
 * Creates a KB first to get an id, then calls the update API to change its name,
 * and finally fetches the updated KB and prints it.
 *
 * Run: npm run run:update   OR   npx ts-node examples/update-knowledge-base/index.ts
 */

import "dotenv/config";
import { Pipeshub } from "@pipeshub-ai/sdk";
import { logger } from "../../src/logger";

// --- Configuration ---

const DEFAULT_KB_NAME = "Sample KB - TypeScript Demo";
const UPDATED_KB_NAME = "Updated - TypeScript Demo";
const DEFAULT_SERVER_URL = "https://app.pipeshub.com/api/v1";
const ENV = {
  BEARER_AUTH: "PIPESHUB_BEARER_AUTH",
  SERVER_URL: "PIPESHUB_SERVER_URL",
} as const;

// --- Client ---

/** Builds a PipesHub client from env (PIPESHUB_BEARER_AUTH required). */
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

// --- Create KB (to get an id) ---

/** Creates a knowledge base and returns its id. */
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

// --- Update KB ---

/** Updates the KB name and logs the updated resource. */
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

// --- Entry point ---

async function main(): Promise<void> {
  const client = getClient();
  const kbId = await createKnowledgeBase(client);
  await updateKnowledgeBase(client, kbId);
}

main().catch((err) => {
  logger.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
});
