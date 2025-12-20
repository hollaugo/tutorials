-- Task Manager v1 schema

create extension if not exists "pgcrypto";

-- updated_at helper
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- Tasks
create table if not exists public.tasks (
  id uuid primary key default gen_random_uuid(),
  user_subject text not null,
  status text not null,
  subject text not null,
  content_md text null,
  due_at timestamptz null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint tasks_status_check check (status in ('not_started','in_progress','completed'))
);

create index if not exists tasks_user_subject_status_idx on public.tasks (user_subject, status);
create index if not exists tasks_user_subject_due_at_idx on public.tasks (user_subject, due_at);

drop trigger if exists set_tasks_updated_at on public.tasks;
create trigger set_tasks_updated_at
before update on public.tasks
for each row execute function public.set_updated_at();

-- Notifications (intent + audit log)
create table if not exists public.notifications (
  id uuid primary key default gen_random_uuid(),
  user_subject text not null,
  task_id uuid null references public.tasks(id) on delete set null,
  type text not null,
  destination text null,
  message text not null,
  scheduled_for timestamptz not null,
  status text not null default 'draft',
  provider_job_id text null,
  provider_payload jsonb null,
  sent_at timestamptz null,
  last_error text null,
  created_at timestamptz not null default now(),
  constraint notifications_type_check check (type in ('chatgpt_task','slack')),
  constraint notifications_status_check check (status in ('draft','scheduled','sent','failed','cancelled'))
);

create index if not exists notifications_user_subject_status_scheduled_for_idx
  on public.notifications (user_subject, status, scheduled_for);
