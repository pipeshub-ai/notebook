/**
 * Example: Get a single knowledge base by id.
 *
 * This script creates a KB first to obtain an id, then fetches that KB
 * and prints its details. Useful to see the get-by-id API in action.
 *
 * Run: npm run run:get   OR   npx ts-node examples/get-knowledge-base/index.ts
 */

import "dotenv/config";
import { Pipeshub } from "@pipeshub-ai/sdk";
import { logger } from "../../src/logger";

// --- Configuration ---

const DEFAULT_KB_NAME = "Sample KB - TypeScript Demo";
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

// --- Get KB by id ---

/** Fetches a knowledge base by id and logs the response. */
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

// --- Entry point ---

async function main(): Promise<void> {
  const client = getClient();
  const kbId = await createKnowledgeBase(client);
  await getKnowledgeBase(client, kbId);
}

main().catch((err) => {
  logger.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
});
