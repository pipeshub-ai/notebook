/**
 * Example: Create a new knowledge base.
 *
 * Calls the API to create a KB with a display name and prints the created resource and its id.
 *
 * Run: npm run run:create   OR   npx ts-node examples/create-knowledge-base/index.ts
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

// --- Create KB ---

/** Creates a knowledge base with the default name and returns its id. */
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

// --- Entry point ---

async function main(): Promise<void> {
  const client = getClient();
  const kbId = await createKnowledgeBase(client);
  logger.info("Created knowledge base id:", kbId);
}

main().catch((err) => {
  logger.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
});
