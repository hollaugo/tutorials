-- Add idempotency support to avoid duplicate task creation due to retries/double-submit.

alter table public.tasks
  add column if not exists idempotency_key text;

create unique index if not exists tasks_user_subject_idempotency_key_uniq
  on public.tasks (user_subject, idempotency_key)
  where idempotency_key is not null;


