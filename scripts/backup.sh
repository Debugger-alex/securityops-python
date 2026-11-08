#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $# -ne 1 ]]; then
    echo "Verwendung: bash scripts/backup.sh <neues-backup-verzeichnis>" >&2
    exit 2
fi

: "${BACKUP_AGE_RECIPIENT:?BACKUP_AGE_RECIPIENT muss gesetzt sein}"
command -v docker >/dev/null || { echo "docker wurde nicht gefunden." >&2; exit 1; }
command -v age >/dev/null || { echo "age wurde nicht gefunden." >&2; exit 1; }

output=$1
if [[ -e "$output" ]]; then
    echo "Zielverzeichnis existiert bereits: $output" >&2
    exit 1
fi

umask 077
output_parent=$(dirname "$output")
output_name=$(basename "$output")
temporary=$(mktemp -d "$output_parent/.${output_name}.tmp.XXXXXX")
api_was_running=false
backup_container_id=""
cleanup() {
    status=$?
    trap - EXIT
    if [[ -n "$backup_container_id" ]]; then
        docker stop "$backup_container_id" >/dev/null || status=1
    fi
    if [[ "$api_was_running" == true ]]; then
        docker compose start api || status=1
    fi
    rm -rf -- "$temporary"
    exit "$status"
}
trap cleanup EXIT

if [[ -n "$(docker compose ps --status running -q api)" ]]; then
    api_was_running=true
    docker compose stop api
fi

docker compose exec -T db sh -ec \
    'pg_dump --format=custom --no-owner --no-acl --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' \
    | age --encrypt --recipient "$BACKUP_AGE_RECIPIENT" >"$temporary/database.dump.age"

docker compose --profile backup build --quiet backup-documents >/dev/null
backup_container_id=$(
    docker compose --profile backup run --detach --rm --no-deps \
        --entrypoint sh backup-documents -c 'sleep infinity'
)
docker exec "$backup_container_id" \
    tar -C /var/lib/securityops/documents -cf - . \
    | age --encrypt --recipient "$BACKUP_AGE_RECIPIENT" >"$temporary/documents.tar.age"
docker stop "$backup_container_id" >/dev/null
backup_container_id=""

if [[ ! -s "$temporary/database.dump.age" || ! -s "$temporary/documents.tar.age" ]]; then
    echo "Mindestens ein verschlüsselter Backup-Bestandteil ist leer." >&2
    exit 1
fi

chmod 600 "$temporary/database.dump.age" "$temporary/documents.tar.age"
chmod 700 "$temporary"
if ! mv "$temporary" "$output"; then
    echo "Backup-Verzeichnis konnte nicht veröffentlicht werden: $output" >&2
    exit 1
fi
if [[ "$api_was_running" == true ]]; then
    docker compose start api
    api_was_running=false
fi
echo "Verschlüsseltes Datenbank- und Dokumentenbackup geschrieben: $output"
