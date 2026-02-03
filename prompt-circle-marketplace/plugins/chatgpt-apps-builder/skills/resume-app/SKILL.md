---
name: chatgpt-app:resume
description: Resume building an in-progress ChatGPT App from a previous session. Loads saved state and continues from where you left off.
---

# Resume Building a ChatGPT App

You are helping the user resume building a ChatGPT App from a previous session.

## Workflow

1. **Load State**
   Read `.chatgpt-app/state.json` from the current project directory.
   If not found, inform the user and suggest `/chatgpt-app:new`.

2. **Display Progress**
   Show:
   - App name and description
   - Current phase
   - Completed items
   - Pending items

3. **Offer Next Steps**
   Based on current phase:

   **Concept Phase:**
   - Refine use cases
   - Add more tools
   - Move to implementation

   **Implementation Phase:**
   - Generate remaining tools
   - Generate remaining widgets
   - Set up database
   - Configure auth

   **Testing Phase:**
   - Generate golden prompts
   - Run validation
   - Run tests

   **Deployment Phase:**
   - Deploy to Render
   - Verify deployment

4. **Continue Work**
   Let user choose what to work on and spawn appropriate agents.

## Progress Display Format

```
## {App Name}

{Description}

### Current Phase: {Phase}

### Progress

**Tools** ({completed}/{total})
- ✓ list-items (validated)
- ○ create-item (planned)

**Widgets** ({completed}/{total})
- ✓ item-list (validated)
- ○ item-form (planned)

**Auth**: {status}
**Database**: {status}
**Validation**: {status}
**Deployment**: {status}

### Next Steps
1. {suggestion}
2. {suggestion}
```

## State Update

After each action, update `.chatgpt-app/state.json` with new progress.
