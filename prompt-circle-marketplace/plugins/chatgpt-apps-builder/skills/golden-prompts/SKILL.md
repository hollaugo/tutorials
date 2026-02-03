---
name: chatgpt-app:golden-prompts
description: Generate test prompts to validate that ChatGPT will correctly invoke your app's tools.
---

# Generate Golden Prompts

You are helping the user generate golden prompts to test their ChatGPT App.

## What Are Golden Prompts?

Test phrases that validate ChatGPT will correctly invoke your app's tools:

1. **Direct Prompts** - Explicitly mention the tool/action
2. **Indirect Prompts** - Describe the goal without naming the tool
3. **Negative Prompts** - Similar phrases that shouldn't trigger the app

## Workflow

1. **Analyze Tools**
   Read the app's tools from state or server code.

2. **Generate Direct Prompts (5+ per tool)**
   Create prompts that explicitly reference the action:
   ```
   "Create a new task called Buy groceries"
   "Add a task for Pick up dry cleaning"
   "Make a new task: Call mom"
   ```

3. **Generate Indirect Prompts (5+ per tool)**
   Create prompts describing the goal:
   ```
   "I need to remember to buy groceries"
   "Don't let me forget to pick up dry cleaning"
   "Remind me to call mom this week"
   ```

4. **Generate Negative Prompts (3+ per category)**
   Create prompts that shouldn't trigger the tool:
   ```
   "What is a task?"
   "How do I prioritize my tasks?"
   "Tell me about task management"
   ```

5. **Save Prompts**
   Write to `.chatgpt-app/golden-prompts.json`

## Output Format

```json
{
  "generatedAt": "2024-01-15T12:00:00Z",
  "tools": {
    "create-task": {
      "direct": ["Create a new task...", ...],
      "indirect": ["I need to remember...", ...],
      "negative": ["What is a task?", ...]
    }
  }
}
```

## Display Summary

```
## Golden Prompts Generated

### create-task
- Direct: 5 prompts
- Indirect: 5 prompts
- Negative: 3 prompts

Total: 30 direct, 30 indirect, 15 negative prompts

Run `/chatgpt-app:test` to validate these prompts.
```
