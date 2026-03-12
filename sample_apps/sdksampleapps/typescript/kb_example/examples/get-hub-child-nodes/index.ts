/**
 * Example: Get child nodes of a knowledge base in the hub.
 *
 * Creates a KB first to get an id, then fetches the child nodes of that KB
 * in the knowledge hub (e.g. connectors or other resources under the KB).
 *
 * Run: npm run run:child-nodes   OR   npx ts-node examples/get-hub-child-nodes/index.ts
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

// --- Get hub child nodes ---

/** Fetches the child nodes of the given KB in the knowledge hub and logs them. */
async function getKnowledgeHubChildNodes(
  pipeshub: Pipeshub,
  kbId: string
): Promise<void> {
  logger.info("Fetching child nodes for knowledge base", { kbId });
  const response = await pipeshub.knowledgeBases.getKnowledgeHubChildNodes({
    parentType: "kb",
    parentId: kbId,
  });
  logger.json("Child nodes", response);
}

// --- Entry point ---

async function main(): Promise<void> {
  const client = getClient();
  const kbId = await createKnowledgeBase(client);
  await getKnowledgeHubChildNodes(client, kbId);
}

main().catch((err) => {
  logger.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
});
