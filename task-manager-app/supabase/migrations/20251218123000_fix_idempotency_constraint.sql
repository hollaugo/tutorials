-- Fix idempotency ON CONFLICT target by using a proper unique constraint.
-- Postgres allows multiple NULLs in UNIQUE constraints, so this works without a partial index.

drop index if exists public.tasks_user_subject_idempotency_key_uniq;

alter table public.tasks
  add constraint tasks_user_subject_idempotency_key_uniq unique (user_subject, idempotency_key);


