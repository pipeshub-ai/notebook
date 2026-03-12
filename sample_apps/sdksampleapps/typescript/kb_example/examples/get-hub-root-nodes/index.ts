/**
 * Example: Get knowledge hub root nodes.
 *
 * Fetches the top-level nodes in the knowledge hub (e.g. knowledge bases,
 * connectors, apps). No KB id is needed; this is a global list for the user.
 *
 * Run: npm run run:root-nodes   OR   npx ts-node examples/get-hub-root-nodes/index.ts
 */

import "dotenv/config";
import { Pipeshub } from "@pipeshub-ai/sdk";
import { logger } from "../../src/logger";

// --- Configuration ---

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

// --- Get hub root nodes ---

/** Fetches and logs the root nodes of the knowledge hub. */
async function getKnowledgeHubRootNodes(pipeshub: Pipeshub): Promise<void> {
  logger.info("Fetching knowledge hub root nodes...");
  const response = await pipeshub.knowledgeBases.getKnowledgeHubRootNodes({});
  logger.json("Root nodes", response);
}

// --- Entry point ---

async function main(): Promise<void> {
  const client = getClient();
  await getKnowledgeHubRootNodes(client);
}

main().catch((err) => {
  logger.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
});
