---
name: chatgpt-app:add-tool
description: Add a new MCP tool to your ChatGPT App. Guides through tool design, schema creation, and code generation.
---

# Add MCP Tool

You are helping the user add a new MCP tool to their ChatGPT App.

## Workflow

1. **Gather Information**
   Ask:
   - What does this tool do?
   - What inputs does it need?
   - What does it return?

2. **Classify Tool Type**
   - **Query** (readOnlyHint: true) - Fetches data
   - **Mutation** (destructiveHint: false) - Creates/updates data
   - **Destructive** (destructiveHint: true) - Deletes data
   - **Widget** - Returns UI content
   - **External** (openWorldHint: true) - Calls external APIs

3. **Design Input Schema**
   Create Zod schema with:
   - Appropriate types
   - Optional fields marked
   - Descriptions for clarity

4. **Generate Tool Handler**
   Use `chatgpt-mcp-generator` agent to create:
   - Tool handler in `server/tools/`
   - Zod schema export
   - Type exports
   - Database queries (if needed)

5. **Register Tool**
   Update `server/index.ts` with proper metadata:
   - openai/toolInvocation/invoking
   - openai/toolInvocation/invoked
   - openai/outputTemplate (for widget tools)

6. **Update State**
   Add tool to `.chatgpt-app/state.json`.

## Tool Naming

Use kebab-case: `list-items`, `create-task`, `show-recipe-detail`

## Annotations Guide

| Scenario | readOnlyHint | destructiveHint | openWorldHint |
|----------|--------------|-----------------|---------------|
| List/Get | true | false | false |
| Create/Update | false | false | false |
| Delete | false | true | false |
| External API | varies | varies | true |

## Widget Tool Pattern

For tools that render UI:
```typescript
{
  name: "show-item-list",
  _meta: {
    "openai/outputTemplate": "ui://widget/item-list.html",
    "openai/toolInvocation/invoking": "Loading...",
    "openai/toolInvocation/invoked": "Done",
  }
}
```
