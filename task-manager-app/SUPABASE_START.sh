#!/bin/bash
#
# Supabase Local bootstrap for Task Manager
# - starts containers
# - applies migrations in supabase/migrations/
# - seeds supabase/seed.sql
#
# Usage:
#   ./SUPABASE_START.sh
#
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v supabase >/dev/null 2>&1; then
  echo "❌ Supabase CLI not found."
  echo "Install it first:"
  echo "  brew install supabase/tap/supabase"
  exit 1
fi

echo "============================================================"
echo "🗄️  Supabase Local - Task Manager"
echo "============================================================"
echo ""

echo "▶ Starting Supabase local..."
supabase start
echo ""

echo "▶ Applying migrations (supabase/migrations/) + seed (supabase/seed.sql)..."
supabase db reset
echo ""

echo "✅ Supabase local is ready."
echo ""
echo "Useful commands:"
echo "  supabase status     # shows DB URL + Studio URL"
echo "  supabase stop       # stop this project's containers"
echo "  supabase stop --all # stop all local supabase projects"
echo ""


