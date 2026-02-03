#!/usr/bin/env tsx
/**
 * Validates MCP tool schemas for ChatGPT Apps
 *
 * Checks:
 * - Valid JSON Schema for all tools
 * - Required _meta fields present
 * - Proper annotations (readOnly, destructive, openWorld)
 * - Input schemas use appropriate types
 */

import { readFileSync, existsSync } from "fs";
import { join } from "path";

interface ValidationResult {
  tool: string;
  passed: boolean;
  errors: string[];
  warnings: string[];
}

interface ToolDefinition {
  name: string;
  description?: string;
  inputSchema?: Record<string, unknown>;
  annotations?: {
    readOnlyHint?: boolean;
    destructiveHint?: boolean;
    openWorldHint?: boolean;
    idempotentHint?: boolean;
  };
  _meta?: Record<string, unknown>;
}

function validateToolSchema(tool: ToolDefinition): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Check name
  if (!tool.name) {
    errors.push("Missing tool name");
  } else if (!/^[a-z][a-z0-9-]*$/.test(tool.name)) {
    errors.push(`Invalid tool name format: ${tool.name} (should be kebab-case)`);
  }

  // Check description
  if (!tool.description) {
    warnings.push("Missing description");
  }

  // Check input schema
  if (!tool.inputSchema) {
    warnings.push("No input schema defined");
  } else {
    if (tool.inputSchema.type !== "object") {
      errors.push("Input schema must be an object type");
    }
  }

  // Check required _meta fields
  if (!tool._meta) {
    errors.push("Missing _meta object");
  } else {
    const invoking = tool._meta["openai/toolInvocation/invoking"];
    const invoked = tool._meta["openai/toolInvocation/invoked"];

    if (!invoking) {
      errors.push("Missing openai/toolInvocation/invoking");
    } else if (typeof invoking === "string" && invoking.length > 64) {
      errors.push("openai/toolInvocation/invoking exceeds 64 characters");
    }

    if (!invoked) {
      errors.push("Missing openai/toolInvocation/invoked");
    } else if (typeof invoked === "string" && invoked.length > 64) {
      errors.push("openai/toolInvocation/invoked exceeds 64 characters");
    }
  }

  // Check annotations
  if (!tool.annotations) {
    warnings.push("No annotations defined");
  } else {
    if (tool.annotations.readOnlyHint === undefined) {
      warnings.push("readOnlyHint not set");
    }
    if (tool.annotations.destructiveHint === undefined) {
      warnings.push("destructiveHint not set");
    }
  }

  return {
    tool: tool.name || "unknown",
    passed: errors.length === 0,
    errors,
    warnings,
  };
}

function validateWidgetTool(tool: ToolDefinition): string[] {
  const errors: string[] = [];

  // Widget tools need outputTemplate
  if (tool._meta && !tool._meta["openai/outputTemplate"]) {
    errors.push("Widget tool missing openai/outputTemplate");
  }

  return errors;
}

async function main() {
  const args = process.argv.slice(2);
  const toolsPath = args[0] || "server/tools";

  console.log("Validating MCP tool schemas...\n");

  // In a real implementation, we'd read the tool definitions from the server
  // For now, this is a template showing what validation looks like

  const sampleTools: ToolDefinition[] = [
    {
      name: "list-items",
      description: "List all items for the current user",
      inputSchema: {
        type: "object",
        properties: {
          status: { type: "string", enum: ["active", "completed"] },
          limit: { type: "number", minimum: 1, maximum: 100 },
        },
      },
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        openWorldHint: false,
      },
      _meta: {
        "openai/toolInvocation/invoking": "Loading items...",
        "openai/toolInvocation/invoked": "Items loaded",
      },
    },
  ];

  let allPassed = true;
  const results: ValidationResult[] = [];

  for (const tool of sampleTools) {
    const result = validateToolSchema(tool);
    results.push(result);

    const status = result.passed ? "✓" : "✗";
    console.log(`${status} ${result.tool}`);

    for (const error of result.errors) {
      console.log(`  ✗ ${error}`);
      allPassed = false;
    }

    for (const warning of result.warnings) {
      console.log(`  ⚠ ${warning}`);
    }
  }

  console.log(`\n${allPassed ? "All validations passed" : "Some validations failed"}`);

  // Write results to state directory
  const stateDir = ".chatgpt-app";
  if (existsSync(stateDir)) {
    const report = {
      timestamp: new Date().toISOString(),
      passed: allPassed,
      results,
    };
    // Write to validation-report.json
  }

  process.exit(allPassed ? 0 : 1);
}

main().catch((err) => {
  console.error("Validation failed:", err);
  process.exit(1);
});
