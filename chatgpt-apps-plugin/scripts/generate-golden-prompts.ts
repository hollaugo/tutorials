#!/usr/bin/env tsx
/**
 * Generates Golden Prompts for ChatGPT App testing
 *
 * Creates:
 * - Direct prompts (explicitly naming tools)
 * - Indirect prompts (describing goals)
 * - Negative prompts (shouldn't trigger app)
 */

import { writeFileSync, mkdirSync, existsSync } from "fs";

interface ToolDefinition {
  name: string;
  description: string;
  type: "query" | "mutation" | "destructive" | "widget" | "external";
}

interface GoldenPrompts {
  direct: string[];
  indirect: string[];
  negative: string[];
}

interface GeneratedPrompts {
  [toolName: string]: GoldenPrompts;
}

function parseToolName(name: string): { action: string; subject: string } {
  const parts = name.split("-");
  return {
    action: parts[0],
    subject: parts.slice(1).join(" "),
  };
}

function generateDirectPrompts(tool: ToolDefinition): string[] {
  const { action, subject } = parseToolName(tool.name);
  const prompts: string[] = [];

  // Action-based prompts
  prompts.push(`${action} a ${subject}`);
  prompts.push(`${action} ${subject}`);
  prompts.push(`Please ${action} a ${subject}`);
  prompts.push(`Can you ${action} a ${subject}?`);
  prompts.push(`I want to ${action} a ${subject}`);

  // Tool name reference
  prompts.push(`Use the ${tool.name} tool`);

  return prompts;
}

function generateIndirectPrompts(tool: ToolDefinition): string[] {
  const { action, subject } = parseToolName(tool.name);
  const prompts: string[] = [];

  switch (action) {
    case "create":
    case "add":
      prompts.push(`I need a new ${subject}`);
      prompts.push(`Make a ${subject} for me`);
      prompts.push(`Set up a ${subject}`);
      prompts.push(`I want a ${subject}`);
      prompts.push(`Add a ${subject} to my list`);
      break;

    case "list":
    case "show":
    case "get":
      prompts.push(`What ${subject}s do I have?`);
      prompts.push(`Show me my ${subject}s`);
      prompts.push(`What are my ${subject}s?`);
      prompts.push(`Display my ${subject}s`);
      prompts.push(`I want to see my ${subject}s`);
      break;

    case "update":
    case "edit":
      prompts.push(`Change my ${subject}`);
      prompts.push(`Modify the ${subject}`);
      prompts.push(`Make changes to my ${subject}`);
      prompts.push(`I need to update a ${subject}`);
      prompts.push(`Edit my ${subject}`);
      break;

    case "delete":
    case "remove":
      prompts.push(`Get rid of the ${subject}`);
      prompts.push(`I don't need this ${subject} anymore`);
      prompts.push(`Take away the ${subject}`);
      prompts.push(`Remove the ${subject}`);
      prompts.push(`Clear out this ${subject}`);
      break;

    default:
      prompts.push(`I need help with ${subject}`);
      prompts.push(`Can you assist with ${subject}?`);
      prompts.push(`Help me with ${subject}`);
  }

  return prompts;
}

function generateNegativePrompts(tool: ToolDefinition): string[] {
  const { subject } = parseToolName(tool.name);
  const prompts: string[] = [];

  // Informational queries (shouldn't trigger action)
  prompts.push(`What is a ${subject}?`);
  prompts.push(`Tell me about ${subject}s`);
  prompts.push(`How do ${subject}s work?`);

  // General questions
  prompts.push(`What's the best way to organize ${subject}s?`);
  prompts.push(`Why are ${subject}s important?`);

  return prompts;
}

async function main() {
  console.log("Generating Golden Prompts...\n");

  // Sample tools - in practice, these would be read from the project
  const tools: ToolDefinition[] = [
    { name: "create-task", description: "Create a new task", type: "mutation" },
    { name: "list-tasks", description: "List all tasks", type: "query" },
    { name: "update-task", description: "Update a task", type: "mutation" },
    { name: "delete-task", description: "Delete a task", type: "destructive" },
    { name: "show-task-board", description: "Show task board", type: "widget" },
  ];

  const allPrompts: GeneratedPrompts = {};
  const combined: GoldenPrompts = {
    direct: [],
    indirect: [],
    negative: [],
  };

  for (const tool of tools) {
    const direct = generateDirectPrompts(tool);
    const indirect = generateIndirectPrompts(tool);
    const negative = generateNegativePrompts(tool);

    allPrompts[tool.name] = { direct, indirect, negative };

    combined.direct.push(...direct);
    combined.indirect.push(...indirect);
    combined.negative.push(...negative);

    console.log(`${tool.name}:`);
    console.log(`  Direct: ${direct.length} prompts`);
    console.log(`  Indirect: ${indirect.length} prompts`);
    console.log(`  Negative: ${negative.length} prompts`);
  }

  console.log(`\nTotal:`);
  console.log(`  Direct: ${combined.direct.length} prompts`);
  console.log(`  Indirect: ${combined.indirect.length} prompts`);
  console.log(`  Negative: ${combined.negative.length} prompts`);

  // Write to state directory
  const stateDir = ".chatgpt-app";
  if (!existsSync(stateDir)) {
    mkdirSync(stateDir, { recursive: true });
  }

  const output = {
    generatedAt: new Date().toISOString(),
    tools: allPrompts,
    combined,
  };

  writeFileSync(
    `${stateDir}/golden-prompts.json`,
    JSON.stringify(output, null, 2)
  );

  console.log(`\nSaved to ${stateDir}/golden-prompts.json`);
}

main().catch((err) => {
  console.error("Generation failed:", err);
  process.exit(1);
});
