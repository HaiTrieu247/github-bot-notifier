#!/usr/bin/env bash
# One-time migration: copy data from the old NeonDB into the self-hosted postgres service.
#
# Safe to run on every deploy — it only does work when BOTH are true:
#   1. The local app_config table is empty (nothing migrated or seeded yet).
#   2. .env has an external source URL: NEON_DATABASE_URL, or the legacy DATABASE_URL.
#
# Schema is created by the app itself (init_db), then only DATA is copied from Neon,
# so Neon-specific objects never reach the local database.
# The copy runs in a single transaction: on any error nothing is written, and the
# next run retries.
#
# Requires the postgres service to be up and the bot image to be built.
#
# Usage: scripts/migrate_from_neon.sh [docker compose args...]
#   e.g. scripts/migrate_from_neon.sh -f docker-compose.yml -f docker-compose.prod.yml

set -euo pipefail

COMPOSE=(docker compose "$@")
ENV_FILE="${ENV_FILE:-.env}"

log() { echo "[migrate] $*"; }

# Print the value of KEY from $ENV_FILE (last occurrence), without surrounding quotes.
read_env() {
  { grep -E "^$1=" "$ENV_FILE" 2>/dev/null || true; } \
    | tail -n 1 | cut -d= -f2- | sed -E "s/^\"(.*)\"$/\1/; s/^'(.*)'$/\1/"
}

# psql against the local database, inside the postgres container.
psql_local() {
  "${COMPOSE[@]}" exec -T postgres \
    sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" "$@"' psql "$@"
}

local_config_rows() {
  if [ "$(psql_local -tAc "SELECT to_regclass('public.app_config') IS NOT NULL")" != "t" ]; then
    echo 0
    return
  fi
  psql_local -tAc "SELECT count(*) FROM app_config"
}

# ── 1. Find the source database ──────────────────────────────────────────────
src_url="$(read_env NEON_DATABASE_URL)"
[ -n "$src_url" ] || src_url="$(read_env DATABASE_URL)"

if [ -z "$src_url" ] || [[ "$src_url" == *"@postgres:"* ]]; then
  log "No external source database in $ENV_FILE — skipping"
  exit 0
fi

# pg_dump (libpq) doesn't understand the SQLAlchemy driver suffix
src_url="${src_url/postgresql+asyncpg:\/\//postgresql://}"

# ── 2. Skip if the local database already has data ───────────────────────────
rows="$(local_config_rows)"
if [ "$rows" -gt 0 ]; then
  log "Local database already has $rows config rows — skipping"
  exit 0
fi

# ── 3. Create schema with the app's own models ───────────────────────────────
log "Creating schema in local database…"
"${COMPOSE[@]}" run --rm --no-deps -T bot \
  python -c "import asyncio; from src.db.main import init_db; asyncio.run(init_db())"

# ── 4. Copy data ─────────────────────────────────────────────────────────────
# Dump to a file first: piping straight into psql would COMMIT a truncated dump
# if pg_dump died halfway. The dump holds tokens/secrets — mktemp makes it 0600.
dump_file="$(mktemp)"
trap 'rm -f "$dump_file"' EXIT

log "Dumping data from source database…"
"${COMPOSE[@]}" exec -T postgres \
  pg_dump --data-only --no-owner --no-privileges --schema=public "$src_url" > "$dump_file"

log "Restoring into local database…"
psql_local --quiet --single-transaction < "$dump_file" > /dev/null

log "Done. Row counts in local database:"
psql_local -c "
  SELECT 'app_config' AS table_name, count(*) FROM app_config
  UNION ALL SELECT 'repositories',  count(*) FROM repositories
  UNION ALL SELECT 'events',        count(*) FROM events
  UNION ALL SELECT 'workflow_runs', count(*) FROM workflow_runs
  UNION ALL SELECT 'deployments',   count(*) FROM deployments"
