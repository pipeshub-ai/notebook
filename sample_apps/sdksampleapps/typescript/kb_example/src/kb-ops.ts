import type { Pipeshub } from "@pipeshub-ai/sdk";
import { logger } from "./logger";

/** Default name used when creating a knowledge base in this sample. */
const DEFAULT_KB_NAME = "Sample KB - TypeScript Demo";

/** Name used when updating a knowledge base in this sample. */
const UPDATED_KB_NAME = "Updated - TypeScript Demo";

/**
 * Creates a new knowledge base.
 * @returns The id of the created knowledge base
 */
export async function createKnowledgeBase(
  pipeshub: Pipeshub
): Promise<string> {
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

/**
 * Lists knowledge bases for the authenticated user.
 * Uses permissions OWNER,ORGANIZER,WRITER, limit 10, sorted by creation time.
 */
export async function listKnowledgeBases(
  pipeshub: Pipeshub
): Promise<void> {
  logger.info("Listing knowledge bases...");
  const response = await pipeshub.knowledgeBases.listKnowledgeBases({
    permissions: "OWNER,ORGANIZER,WRITER",
    limit: 10,
    sortBy: "createdAtTimestamp",
  });
  logger.json("Knowledge bases", response);
}

/**
 * Fetches a single knowledge base by id.
 */
export async function getKnowledgeBase(
  pipeshub: Pipeshub,
  kbId: string
): Promise<void> {
  logger.info("Fetching knowledge base", { kbId });
  const response = await pipeshub.knowledgeBases.getKnowledgeBase({
    kbId,
  });
  logger.json("Knowledge base", response);
}

/**
 * Updates a knowledge base (e.g. name) and logs the result.
 */
export async function updateKnowledgeBase(
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

/**
 * Fetches the root nodes of the knowledge hub (top-level KBs, connectors, apps).
 */
export async function getKnowledgeHubRootNodes(
  pipeshub: Pipeshub
): Promise<void> {
  logger.info("Fetching knowledge hub root nodes...");
  const response =
    await pipeshub.knowledgeBases.getKnowledgeHubRootNodes({});
  logger.json("Root nodes", response);
}

/**
 * Fetches the child nodes of a knowledge base in the hub.
 */
export async function getKnowledgeHubChildNodes(
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

/**
 * Deletes a knowledge base by id.
 */
export async function deleteKnowledgeBase(
  pipeshub: Pipeshub,
  kbId: string
): Promise<void> {
  logger.info("Deleting knowledge base", { kbId });
  await pipeshub.knowledgeBases.deleteKnowledgeBase({ kbId });
  logger.info("Knowledge base deleted successfully.");
}
