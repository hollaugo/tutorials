import { existsSync, readFileSync } from "fs";
import path from "path";

const appRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");

const requiredFiles = [
  "package.json",
  "tsconfig.server.json",
  "setup.sh",
  "START.sh",
  ".env.example",
  ".gitignore",
  "server/index.ts",
];

const missing = requiredFiles.filter((file) => !existsSync(path.join(appRoot, file)));

if (missing.length) {
  console.error("CRITICAL: Missing required files:");
  missing.forEach((file) => console.error(` - ${file}`));
  process.exit(1);
}

const serverFile = path.join(appRoot, "server/index.ts");
const serverSource = readFileSync(serverFile, "utf8");

const checks: Array<{ label: string; ok: boolean; required?: boolean }> = [
  {
    label: "Uses Server from @modelcontextprotocol/sdk",
    ok: serverSource.includes("@modelcontextprotocol/sdk/server/index.js"),
    required: true,
  },
  {
    label: "Uses StreamableHTTPServerTransport",
    ok: serverSource.includes("StreamableHTTPServerTransport"),
    required: true,
  },
  {
    label: "Session management Map present",
    ok: /Map<string,\s*StreamableHTTPServerTransport>/.test(serverSource),
    required: true,
  },
  {
    label: "Widget URI format present",
    ok: /ui:\/\/widget\/[^\s"']+\.html/.test(serverSource),
  },
  {
    label: "Widget MIME type present",
    ok: serverSource.includes("text/html+skybridge"),
  },
  {
    label: "Tool responses include structuredContent",
    ok: serverSource.includes("structuredContent"),
  },
  {
    label: "Preview endpoints present",
    ok: serverSource.includes("/preview") && serverSource.includes("/preview/:widgetId"),
  },
  {
    label: "Does not use McpServer",
    ok: !serverSource.includes("McpServer"),
    required: true,
  },
];

const failedRequired = checks.filter((check) => check.required && !check.ok);

console.log("\n## Validation Results\n");
checks.forEach((check) => {
  console.log(`${check.ok ? "✓" : "✗"} ${check.label}`);
});

if (failedRequired.length) {
  console.error("\nOverall: FAIL (required checks failed)");
  process.exit(1);
}

console.log("\nOverall: PASS");
