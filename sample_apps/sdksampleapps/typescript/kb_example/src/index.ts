import "dotenv/config";
import { Pipeshub } from "@pipeshub-ai/sdk";

async function createKnowledgeBase(pipeshub: Pipeshub): Promise<string> {
  console.log("\n--- Create Knowledge Base ---");
  const res = await pipeshub.knowledgeBases.createKnowledgeBase({
    kbName: "Sample KB - TypeScript Demo",
  });
  const kbId = res.id ?? "";
  if (!kbId) throw new Error("Create response missing id");
  console.log(JSON.stringify(res, null, 2));
  return kbId;
}

async function listKnowledgeBases(pipeshub: Pipeshub): Promise<void> {
  console.log("\n--- List Knowledge Bases ---");
  const res = await pipeshub.knowledgeBases.listKnowledgeBases({
    permissions: "OWNER,ORGANIZER,WRITER",
    limit: 10,
    sortBy: "createdAtTimestamp",
  });
  console.log(JSON.stringify(res, null, 2));
}

async function getKnowledgeBase(
  pipeshub: Pipeshub,
  kbId: string
): Promise<void> {
  console.log("\n--- Get Knowledge Base ---");
  const res = await pipeshub.knowledgeBases.getKnowledgeBase({ kbId });
  console.log(JSON.stringify(res, null, 2));
}

async function updateKnowledgeBase(
  pipeshub: Pipeshub,
  kbId: string
): Promise<void> {
  const newName = "Updated - TypeScript Demo";
  console.log("\n--- Update Knowledge Base ---");
  console.log("Request: PATCH name ->", JSON.stringify(newName));
  await pipeshub.knowledgeBases.updateKnowledgeBase({
    kbId,
    body: { kbName: newName },
  });
  const updated = await pipeshub.knowledgeBases.getKnowledgeBase({ kbId });
  console.log("Response (get after update):");
  console.log(JSON.stringify(updated, null, 2));
}

async function getKnowledgeHubRootNodes(
  pipeshub: Pipeshub
): Promise<void> {
  console.log("\n--- Get Knowledge Hub Root Nodes ---");
  const res = await pipeshub.knowledgeBases.getKnowledgeHubRootNodes({});
  console.log(JSON.stringify(res, null, 2));
}

async function getKnowledgeHubChildNodes(
  pipeshub: Pipeshub,
  kbId: string
): Promise<void> {
  console.log("\n--- Get Knowledge Hub Child Nodes ---");
  const res = await pipeshub.knowledgeBases.getKnowledgeHubChildNodes({
    parentType: "kb",
    parentId: kbId,
  });
  console.log(JSON.stringify(res, null, 2));
}

async function deleteKnowledgeBase(
  pipeshub: Pipeshub,
  kbId: string
): Promise<void> {
  console.log("\n--- Delete Knowledge Base ---");
  await pipeshub.knowledgeBases.deleteKnowledgeBase({ kbId });
}

const USAGE = `
Usage: npm run dev [command [...]]   or   npx ts-node src/index.ts [command [...]]

Commands (run one or more in order):
  create         Create a new knowledge base (prints id)
  list           List knowledge bases
  get <kbId>     Get a single KB by id
  update <kbId>  Update KB name
  root-nodes     Get knowledge hub root nodes
  child-nodes <kbId>  Get child nodes of a KB
  delete <kbId>  Delete a knowledge base
  all            Run full flow: create → list → get → update → root-nodes → child-nodes → delete (default)

Examples:
  npm run dev                    # full flow
  npm run dev create list        # create then list
  npm run dev list               # list only
  npm run dev get MY-KB-ID       # get one KB
  KB_ID=my-kb-id npm run dev get update child-nodes delete
`;

function parseArgs(): string[] {
  const args = process.argv.slice(2);
  if (args.length === 0) return ["all"];
  if (args[0] === "--help" || args[0] === "-h") {
    console.log(USAGE);
    process.exit(0);
  }
  return args;
}

function getKbId(args: string[], index: number, createdId: string | null): string {
  if (createdId) return createdId;
  const envId = process.env.KB_ID;
  if (envId) return envId;
  const argId = args[index];
  if (argId && !argId.startsWith("-")) return argId;
  throw new Error("KB ID required. Pass as next argument or set KB_ID env var.");
}

async function main(): Promise<void> {
  const bearerAuth = process.env.PIPESHUB_BEARER_AUTH;
  const serverUrl =
    process.env.PIPESHUB_SERVER_URL ?? "https://app.pipeshub.com/api/v1";

  if (!bearerAuth) {
    console.error("PIPESHUB_BEARER_AUTH environment variable is required");
    process.exit(1);
  }

  const pipeshub = new Pipeshub({
    security: { bearerAuth },
    ...(serverUrl && { serverURL: serverUrl }),
  });

  const args = parseArgs();
  let createdKbId: string | null = null;
  let argIndex = 0;

  try {
    while (argIndex < args.length) {
      const cmd = args[argIndex].toLowerCase();
      switch (cmd) {
        case "create": {
          createdKbId = await createKnowledgeBase(pipeshub);
          argIndex += 1;
          break;
        }
        case "list": {
          await listKnowledgeBases(pipeshub);
          argIndex += 1;
          break;
        }
        case "get": {
          const kbId = getKbId(args, argIndex + 1, createdKbId);
          if (args[argIndex + 1] === kbId) argIndex += 1;
          await getKnowledgeBase(pipeshub, kbId);
          argIndex += 1;
          break;
        }
        case "update": {
          const kbId = getKbId(args, argIndex + 1, createdKbId);
          if (args[argIndex + 1] === kbId) argIndex += 1;
          await updateKnowledgeBase(pipeshub, kbId);
          argIndex += 1;
          break;
        }
        case "root-nodes": {
          await getKnowledgeHubRootNodes(pipeshub);
          argIndex += 1;
          break;
        }
        case "child-nodes": {
          const kbId = getKbId(args, argIndex + 1, createdKbId);
          if (args[argIndex + 1] === kbId) argIndex += 1;
          await getKnowledgeHubChildNodes(pipeshub, kbId);
          argIndex += 1;
          break;
        }
        case "delete": {
          const kbId = getKbId(args, argIndex + 1, createdKbId);
          if (args[argIndex + 1] === kbId) argIndex += 1;
          await deleteKnowledgeBase(pipeshub, kbId);
          argIndex += 1;
          break;
        }
        case "all": {
          createdKbId = await createKnowledgeBase(pipeshub);
          await listKnowledgeBases(pipeshub);
          await getKnowledgeBase(pipeshub, createdKbId);
          await updateKnowledgeBase(pipeshub, createdKbId);
          await getKnowledgeHubRootNodes(pipeshub);
          await getKnowledgeHubChildNodes(pipeshub, createdKbId);
          await deleteKnowledgeBase(pipeshub, createdKbId);
          argIndex = args.length;
          break;
        }
        default:
          console.error("Unknown command:", cmd);
          console.log(USAGE);
          process.exit(1);
      }
    }
    console.log("\nDone!");
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error("Failed:", msg);
    process.exit(1);
  }
}

main();
