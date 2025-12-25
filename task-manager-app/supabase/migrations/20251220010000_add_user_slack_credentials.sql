-- Per-user Slack credentials for multi-user mode (OAuth-backed identity).
-- NOTE: For production, consider encrypting tokens at rest (e.g. with Vault / KMS).

create table if not exists public.user_slack_credentials (
  user_subject text primary key,
  slack_bot_token text not null,
  slack_default_channel text null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

drop trigger if exists set_user_slack_credentials_updated_at on public.user_slack_credentials;
create trigger set_user_slack_credentials_updated_at
before update on public.user_slack_credentials
for each row execute function public.set_updated_at();




