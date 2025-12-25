-- Persist OAuth client registrations (dynamic client registration)
-- This prevents "Client ID not found" errors after server restarts.

create table if not exists public.oauth_clients (
  client_id text primary key,
  client_secret text not null,
  client_info jsonb not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

drop trigger if exists set_oauth_clients_updated_at on public.oauth_clients;
create trigger set_oauth_clients_updated_at
before update on public.oauth_clients
for each row execute function public.set_updated_at();




