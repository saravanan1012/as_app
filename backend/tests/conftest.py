import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Use dedicated test DB when available
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg2://as:as_dev@localhost:5433/as_app",
)
os.environ.setdefault("AUTH_SECRET", "test-secret-phase1-min-32-characters!!")


@pytest.fixture(scope="session")
def engine():
    from app.config import get_settings

    get_settings.cache_clear()
    eng = create_engine(get_settings().database_url, pool_pre_ping=True)
    with eng.connect() as conn:
        conn.execute(text("SELECT 1"))
    return eng


@pytest.fixture(scope="session")
def db_ready(engine):
    """Ensure migrations + seed applied (docker entrypoint usually did this)."""
    from app.db import SessionLocal
    from app.seed import run_seed

    db = SessionLocal()
    try:
        run_seed(db)
    finally:
        db.close()
    return True


@pytest.fixture
def client(db_ready):
    from app.config import get_settings
    from app.main import app

    get_settings.cache_clear()
    with TestClient(app) as c:
        yield c
