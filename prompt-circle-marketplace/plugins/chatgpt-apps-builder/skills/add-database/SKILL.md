---
name: chatgpt-app:add-database
description: Configure a PostgreSQL database for your ChatGPT App using Supabase for data persistence.
---

# Configure Database

You are helping the user add a PostgreSQL database to their ChatGPT App using Supabase.

## When to Add Database

- App needs to persist user data
- Data survives across conversations
- Multiple entities with relationships
- Query and filter capabilities needed

## Workflow

1. **Check Supabase Setup**
   Ask:
   - "Do you have a Supabase project?"
   - If no, guide them to create one at supabase.com

2. **Gather Credentials**
   - Project URL
   - Anon Key (public)
   - Service Key (private, server-side)

3. **Define Entities**
   For each entity, gather:
   - Name (e.g., "Task", "Recipe")
   - Fields and types
   - Relationships to other entities

4. **Generate Schema**
   Use `chatgpt-schema-designer` agent to create:
   - SQL migrations in `supabase/migrations/`
   - TypeScript types
   - Query helpers

5. **Generate Connection Pool**
   Create `server/db/pool.ts`.

6. **Setup Local Development**
   Create Supabase config and start scripts.

7. **Apply Migrations**
   ```bash
   supabase start
   supabase db reset
   ```

## Schema Requirements

Every table MUST have:
- `id UUID PRIMARY KEY`
- `user_subject TEXT NOT NULL` (for data isolation)
- `created_at TIMESTAMPTZ`
- `updated_at TIMESTAMPTZ`
- Index on `(user_subject)`

## Environment Variables

```
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
```

## Query Pattern

Always filter by user_subject:
```sql
SELECT * FROM tasks WHERE user_subject = $1
```
