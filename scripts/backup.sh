#!/usr/bin/env bash
set -euo pipefail

readonly REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
readonly COMPOSE_FILE="${REPO_DIR}/docker-compose.prod.yml"
readonly TS=$(date -u +%Y%m%dT%H%M%SZ)
readonly BACKUP_FILE="/tmp/db-${TS}.sql.gz"
readonly R2_BUCKET="r2:gbp-pilot-review-backup"

cd "$REPO_DIR"

# Charge POSTGRES_USER/DB depuis le .env
export $(grep -E '^POSTGRES_(USER|DB)=' .env | xargs)

echo "[INFO] Dump de la DB ${POSTGRES_DB}..."
docker compose -f "$COMPOSE_FILE" exec -T postgres \
    pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" \
    | gzip > "$BACKUP_FILE"

readonly SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "[INFO] Dump créé : $BACKUP_FILE ($SIZE)"

echo "[INFO] Upload vers $R2_BUCKET..."
rclone copy "$BACKUP_FILE" "$R2_BUCKET"

rm "$BACKUP_FILE"
echo "[INFO] Backup terminé ✅"
