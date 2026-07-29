#!/usr/bin/env bash
set -Eeuo pipefail

version="${1:-}"
next_compose="${2:-}"
deploy_dir="${DEPLOY_DIR:-/opt/werss}"
project_name="${COMPOSE_PROJECT_NAME:-werss}"

if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Invalid release version: $version" >&2
    exit 2
fi

if [[ "$deploy_dir" != /* ]]; then
    echo "DEPLOY_DIR must be an absolute path" >&2
    exit 2
fi

if [[ -z "$next_compose" || ! -f "$next_compose" ]]; then
    echo "Compose candidate not found: $next_compose" >&2
    exit 2
fi

env_file="$deploy_dir/.env"
release_file="$deploy_dir/.release.env"
next_release_file="$deploy_dir/.release.env.next"
current_compose="$deploy_dir/docker-compose.yml"
rollback_dir="$deploy_dir/.rollback"
rollback_compose="$rollback_dir/docker-compose.yml"
rollback_release="$rollback_dir/.release.env"
backup_dir="$deploy_dir/backups"

if [[ ! -f "$env_file" ]]; then
    echo "Production configuration is missing: $env_file" >&2
    exit 2
fi

mkdir -p "$backup_dir" "$rollback_dir"
chmod 0750 "$backup_dir" "$rollback_dir"

umask 077
printf 'WERSS_IMAGE_TAG=%s\n' "$version" > "$next_release_file"

compose_with() {
    local compose_file="$1"
    local release_env="$2"
    shift 2
    docker compose \
        --project-name "$project_name" \
        --project-directory "$deploy_dir" \
        --env-file "$env_file" \
        --env-file "$release_env" \
        -f "$compose_file" \
        "$@"
}

backup_database() {
    if [[ ! -f "$current_compose" || ! -f "$release_file" ]]; then
        echo "No previous deployment; database backup is not required."
        return
    fi

    local postgres_id
    postgres_id="$(
        compose_with "$current_compose" "$release_file" \
            ps --status running --quiet postgres 2>/dev/null || true
    )"
    if [[ -z "$postgres_id" ]]; then
        echo "PostgreSQL is not running in this Compose project; skipping pg_dump."
        return
    fi

    local timestamp backup_tmp backup_file
    timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
    backup_tmp="$backup_dir/postgres-${timestamp}-before-${version}.sql.gz.tmp"
    backup_file="${backup_tmp%.tmp}"

    echo "Creating PostgreSQL backup: $backup_file"
    if ! compose_with "$current_compose" "$release_file" \
        exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' \
        | gzip -c > "$backup_tmp"; then
        rm -f "$backup_tmp"
        echo "Database backup failed; deployment aborted before changing containers." >&2
        exit 1
    fi
    mv "$backup_tmp" "$backup_file"
    chmod 0600 "$backup_file"
}

rollback_armed=0
rollback() {
    local status=$?
    trap - ERR

    if [[ "$rollback_armed" -eq 1 && -f "$rollback_compose" && -f "$rollback_release" ]]; then
        echo "Deployment failed; restoring the previous Compose definition and image version." >&2
        compose_with "$rollback_compose" "$rollback_release" \
            up --detach --no-build --wait --wait-timeout 300 --remove-orphans || true
    else
        echo "Deployment failed and no previous release is available for automatic image rollback." >&2
    fi
    exit "$status"
}
trap rollback ERR

compose_with "$next_compose" "$next_release_file" config --quiet
backup_database

if [[ -f "$current_compose" && -f "$release_file" ]]; then
    install -m 0644 "$current_compose" "$rollback_compose"
    install -m 0600 "$release_file" "$rollback_release"
fi

echo "Pulling WeRSS release $version and pinned infrastructure images."
compose_with "$next_compose" "$next_release_file" pull

rollback_armed=1
compose_with "$next_compose" "$next_release_file" \
    up --detach --no-build --wait --wait-timeout 300 --remove-orphans

compose_with "$next_compose" "$next_release_file" \
    exec -T werss curl -fsS http://127.0.0.1:8001/api/health >/dev/null

actual_version="$(
    compose_with "$next_compose" "$next_release_file" exec -T werss \
        python3 -c \
        'import json, urllib.request; print(json.load(urllib.request.urlopen("http://127.0.0.1:8001/api/v1/sys/version"))["core_version"])'
)"
if [[ "$actual_version" != "$version" ]]; then
    echo "Version check failed: expected $version, got $actual_version" >&2
    false
fi

install -m 0644 "$next_compose" "$current_compose"
install -m 0600 "$next_release_file" "$release_file"
install -m 0755 "$0" "$deploy_dir/deploy-production.sh"
rollback_armed=0

echo "WeRSS $version is healthy and active."
