#!/usr/bin/env bash
set -euo pipefail

APP_NAME="as_app"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

WEB_URL="${WEB_URL:-http://localhost:3000}"
API_HEALTH_URL="${API_HEALTH_URL:-http://localhost:8000/api/health}"
MAX_ATTEMPTS="${HEALTH_ATTEMPTS:-60}"
SLEEP_SECONDS="${HEALTH_SLEEP:-3}"

usage() {
  cat <<EOF
Usage: $(basename "$0") [up|down|logs|status|test]

  up      Build and start db + api + web (default)
  down    Stop stack (keeps volumes)
  logs    Tail api + web logs
  status  Show compose status + health URLs
  test    Run pytest in the api container
EOF
}

need_docker() {
  command -v docker >/dev/null 2>&1 || {
    echo "[$APP_NAME] docker is required" >&2
    exit 1
  }
  docker compose version >/dev/null 2>&1 || {
    echo "[$APP_NAME] docker compose is required" >&2
    exit 1
  }
}

wait_health() {
  local url="$1" name="$2" i=1
  echo "[$APP_NAME] Waiting for ${name} (${url})..."
  while [ "$i" -le "$MAX_ATTEMPTS" ]; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "[$APP_NAME] ${name} is up"
      return 0
    fi
    sleep "$SLEEP_SECONDS"
    i=$((i + 1))
  done
  echo "[$APP_NAME] Timed out waiting for ${name}" >&2
  docker compose ps
  docker compose logs --tail=50 api web || true
  exit 1
}

cmd="${1:-up}"

need_docker

case "$cmd" in
  up)
    echo "[$APP_NAME] Starting local stack in ${ROOT}"
    docker compose up -d --build
    wait_health "$API_HEALTH_URL" "API"
    echo "[$APP_NAME] Web:  ${WEB_URL}"
    echo "[$APP_NAME] API:  ${API_HEALTH_URL}"
    echo "[$APP_NAME] Login: superadmin@as.com / User@123"
    ;;
  down)
    docker compose down
    echo "[$APP_NAME] Stopped (volumes kept)"
    ;;
  logs)
    docker compose logs -f --tail=100 api web
    ;;
  status)
    docker compose ps
    echo "Web: ${WEB_URL}"
    echo "API: ${API_HEALTH_URL}"
    ;;
  test)
    docker compose exec -T api pytest -q
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    echo "[$APP_NAME] Unknown command: $cmd" >&2
    usage >&2
    exit 1
    ;;
esac
