---
name: chatgpt-app:test
description: Run automated tests on your ChatGPT App using MCP Inspector and golden prompt validation.
---

# Test ChatGPT App

You are helping the user run automated tests on their ChatGPT App.

## Test Categories

### 1. MCP Protocol Tests
- Tool Discovery - List all tools
- Tool Execution - Call each tool
- Error Handling - Test invalid inputs
- Resource Listing - Verify widgets exist

### 2. Schema Tests
- Validate input schemas
- Check type constraints
- Test required fields

### 3. Widget Tests
- HTML is valid
- JavaScript bundles load
- React components render
- Theme switching works

### 4. Golden Prompt Tests
- Direct prompts trigger correct tools
- Indirect prompts trigger correct tools
- Negative prompts don't trigger tools

## Workflow

1. **Start Server in Test Mode**
   ```bash
   npm run start:stdio
   ```

2. **Run MCP Inspector Tests**
   Use `chatgpt-test-runner` agent.

3. **Run Schema Validation**
   Check all tool schemas.

4. **Run Golden Prompt Tests**
   Validate prompts from `.chatgpt-app/golden-prompts.json`.

5. **Generate Report**
   Save to `.chatgpt-app/test-report.json`.

## Results Format

```
## Test Results

### MCP Protocol Tests
✓ Tool discovery (15ms)
✓ list-items execution (45ms)
✓ create-item execution (52ms)

### Golden Prompt Tests
Direct: 15/15 passed
Indirect: 14/15 passed
Negative: 9/9 rejected

---
**Overall: 38/39 tests passed**
```

## Fixing Failures

For each failure, explain:
- What failed
- Why it failed
- How to fix it with code example
