import "dotenv/config";
import { Pipeshub } from "@pipeshub-ai/sdk";
import { logger } from "./logger";

/** Default PipesHub API base URL. */
const DEFAULT_SERVER_URL = "https://app.pipeshub.com/api/v1";

/** Environment variable names used by this sample. */
export const ENV = {
  BEARER_AUTH: "PIPESHUB_BEARER_AUTH",
  SERVER_URL: "PIPESHUB_SERVER_URL",
  KB_ID: "KB_ID",
} as const;

/**
 * Creates and returns a configured PipesHub client.
 *
 * Loads environment from `.env` (via dotenv). Requires `PIPESHUB_BEARER_AUTH`.
 * Optionally set `PIPESHUB_SERVER_URL` to override the API base URL.
 *
 * @returns Configured Pipeshub instance
 * @throws Error if `PIPESHUB_BEARER_AUTH` is missing or empty
 */
export function getClient(): Pipeshub {
  const bearerAuth = process.env[ENV.BEARER_AUTH];

  if (!bearerAuth?.trim()) {
    logger.error(
      `Missing required environment variable: ${ENV.BEARER_AUTH}. Set it in .env or your shell.`
    );
    throw new Error(`Required: ${ENV.BEARER_AUTH}`);
  }

  const serverUrl =
    process.env[ENV.SERVER_URL]?.trim() || DEFAULT_SERVER_URL;

  return new Pipeshub({
    security: { bearerAuth: bearerAuth.trim() },
    serverURL: serverUrl,
  });
}
