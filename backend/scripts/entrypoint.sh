#!/bin/sh
set -eu
cd /app
alembic upgrade head
# Production can set SKIP_SEED=1 after bootstrap/ETL (seed is idempotent either way).
if [ "${SKIP_SEED:-0}" != "1" ]; then
  python -c "from app.db import SessionLocal; from app.seed import run_seed; db=SessionLocal(); run_seed(db); db.close()"
fi
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
