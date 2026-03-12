import type { Pipeshub } from "@pipeshub-ai/sdk";
import { ENV } from "./client";
import { createKnowledgeBase } from "./kb-ops";
import { logger } from "./logger";

const DEFAULT_ARGV_INDEX = 2;

/**
 * Resolves the knowledge base ID from environment or command-line.
 * Use when you require an explicit id (e.g. scripts that must not create a KB).
 *
 * Resolution order: `KB_ID` env var, then first script argument.
 *
 * @param argvIndex - Index in process.argv for the KB id (default 2)
 * @returns The resolved KB id
 * @exits process with code 1 if no id is provided
 */
export function resolveKbId(argvIndex: number = DEFAULT_ARGV_INDEX): string {
  const kbId = getKbIdFromEnvOrArgv(argvIndex);
  if (!kbId) {
    logger.error(
      `Knowledge base ID required. Set ${ENV.KB_ID} or pass the id as the first argument.`
    );
    process.exit(1);
  }
  return kbId;
}

/**
 * Returns a KB id to use: from env/argv if set, otherwise creates a new knowledge base and returns its id.
 * Use this in examples so they work with no arguments (create and use a new KB when id is not given).
 *
 * @param client - Configured Pipeshub client (used to create a KB when no id is provided)
 * @param argvIndex - Index in process.argv for the KB id (default 2)
 * @returns The existing or newly created knowledge base id
 */
export async function getKbIdOrCreate(
  client: Pipeshub,
  argvIndex: number = DEFAULT_ARGV_INDEX
): Promise<string> {
  const existing = getKbIdFromEnvOrArgv(argvIndex);
  if (existing) return existing;
  logger.info("No KB id provided; creating a new knowledge base for this run.");
  return createKnowledgeBase(client);
}

function getKbIdFromEnvOrArgv(argvIndex: number): string {
  const fromEnv = process.env[ENV.KB_ID]?.trim();
  const fromArgv = process.argv[argvIndex]?.trim();
  return fromEnv || fromArgv || "";
}
