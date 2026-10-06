#!/usr/bin/env bash
set -euo pipefail

APP_NAME="as_app"
DEPLOY_PATH="${DEPLOY_PATH:-$(pwd)}"
BRANCH="${DEPLOY_BRANCH:-main}"
ENV_FILE="${DEPLOY_ENV_FILE:-.env.prd}"
COMPOSE_FILE="${DEPLOY_COMPOSE_FILE:-docker-compose.prd.yml}"
WEB_CONTAINER="${DEPLOY_WEB_CONTAINER:-as_app_web}"
API_CONTAINER="${DEPLOY_API_CONTAINER:-as_app_api}"
DB_CONTAINER="${DEPLOY_DB_CONTAINER:-as_app_db}"
# Host publishes web on :3001. On this VPS 127.0.0.1:3001 is unreliable —
# use the public host IP for nginx + health (same pattern as legacy AS).
AS_UPSTREAM_URL="${AS_UPSTREAM_URL:-http://94.249.213.162:3001}"
HEALTH_URL="${DEPLOY_HEALTH_URL:-${AS_UPSTREAM_URL}/}"
API_HEALTH_URL="${DEPLOY_API_HEALTH_URL:-${AS_UPSTREAM_URL}/api/health}"
MAX_ATTEMPTS="${DEPLOY_HEALTH_ATTEMPTS:-60}"
SLEEP_SECONDS="${DEPLOY_HEALTH_SLEEP:-3}"

echo "[$APP_NAME] Starting deployment in ${DEPLOY_PATH}"
echo "[$APP_NAME] NEVER use 'docker compose down -v' on VPS (destroys Postgres data)."

cd "${DEPLOY_PATH}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "[$APP_NAME] Not a git repository: ${DEPLOY_PATH}" >&2
  exit 1
fi

if [ ! -f "${ENV_FILE}" ]; then
  echo "[$APP_NAME] Missing env file: ${ENV_FILE} (copy from .env.prd.example)" >&2
  exit 1
fi

if [ ! -f "${COMPOSE_FILE}" ]; then
  echo "[$APP_NAME] Missing compose file: ${COMPOSE_FILE}" >&2
  exit 1
fi

if grep -E '^(AUTH_URL|NUXT_PUBLIC_APP_URL)=http://(127\.0\.0\.1|localhost)' "${ENV_FILE}" >/dev/null 2>&1; then
  echo "[$APP_NAME] ${ENV_FILE} has localhost Auth/App URLs — refusing VPS deploy." >&2
  echo "[$APP_NAME] Use https://as.hindupanjang.com (or your production origin)." >&2
  exit 1
fi

echo "[$APP_NAME] Fetching latest code from origin/${BRANCH}"
git fetch origin
git checkout "${BRANCH}"
git pull --ff-only origin "${BRANCH}"

NGINX_SITE="${AS_NGINX_SITE:-/etc/nginx/sites-available/as.hindupanjang.com}"
if [ -f "${NGINX_SITE}" ]; then
  echo "[$APP_NAME] Ensuring nginx proxy_pass -> ${AS_UPSTREAM_URL}"
  sed -i -E "s|proxy_pass http://[^;]+;|proxy_pass ${AS_UPSTREAM_URL};|g" "${NGINX_SITE}"
  if command -v nginx >/dev/null 2>&1; then
    nginx -t && systemctl reload nginx || echo "[$APP_NAME] WARN: nginx reload failed" >&2
  fi
fi

echo "[$APP_NAME] Building and restarting containers (volumes preserved)"
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d --build

echo "[$APP_NAME] Waiting for health (web=${HEALTH_URL} api=${API_HEALTH_URL})"
for attempt in $(seq 1 "${MAX_ATTEMPTS}"); do
  web_status="$(docker inspect --format='{{.State.Status}}' "${WEB_CONTAINER}" 2>/dev/null || echo "missing")"
  api_status="$(docker inspect --format='{{.State.Status}}' "${API_CONTAINER}" 2>/dev/null || echo "missing")"
  restart_count="$(docker inspect --format='{{.RestartCount}}' "${WEB_CONTAINER}" 2>/dev/null || echo "?")"
  oom="$(docker inspect --format='{{.State.OOMKilled}}' "${WEB_CONTAINER}" 2>/dev/null || echo "?")"

  if [ "${web_status}" = "restarting" ] || [ "${api_status}" = "restarting" ] || [ "${oom}" = "true" ]; then
    echo "[$APP_NAME] Container unhealthy (web=${web_status} api=${api_status} restarts=${restart_count} oom=${oom})" >&2
    docker logs --tail 80 "${WEB_CONTAINER}" || true
    docker logs --tail 80 "${API_CONTAINER}" || true
    exit 1
  fi

  web_ok=0
  api_ok=0
  curl -4 -fsS --max-time 5 "${HEALTH_URL}" >/dev/null 2>&1 && web_ok=1
  curl -4 -fsS --max-time 5 "${API_HEALTH_URL}" >/dev/null 2>&1 && api_ok=1

  if [ "${web_ok}" = "1" ] && [ "${api_ok}" = "1" ]; then
    echo "[$APP_NAME] Deployment successful (web+api health ok)"
    docker stats --no-stream "${WEB_CONTAINER}" "${API_CONTAINER}" "${DB_CONTAINER}" || true
    exit 0
  fi

  # Fallback: in-network probes (host curl may fail while containers are fine)
  if docker exec "${API_CONTAINER}" python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3)" 2>/dev/null \
    && docker exec "${WEB_CONTAINER}" wget -q -O /dev/null http://127.0.0.1:3000/ 2>/dev/null; then
    echo "[$APP_NAME] Deployment successful (in-container probes ok; host curl web=${web_ok} api=${api_ok})"
    echo "[$APP_NAME] NOTE: if host curl failed, check nginx / publish :3001 → ${AS_UPSTREAM_URL}"
    docker stats --no-stream "${WEB_CONTAINER}" "${API_CONTAINER}" "${DB_CONTAINER}" || true
    exit 0
  fi

  echo "[$APP_NAME] Health attempt ${attempt}/${MAX_ATTEMPTS} (web=${web_status} api=${api_status} curl_web=${web_ok} curl_api=${api_ok})"
  sleep "${SLEEP_SECONDS}"
done

echo "[$APP_NAME] Health check failed after deploy" >&2
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps || true
docker logs --tail 120 "${API_CONTAINER}" || true
docker logs --tail 120 "${WEB_CONTAINER}" || true
exit 1
