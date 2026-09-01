"""
Shared test fixtures: in-memory SQLite DB, test client, seeded database.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.seed import seed_database

# In-memory SQLite for tests — StaticPool shares a single connection
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create tables and seed BEFORE importing app (which has on_startup)
from app import models  # noqa — registers models with Base
Base.metadata.create_all(bind=engine)

_seed_db = TestingSessionLocal()
seed_database(_seed_db)
_seed_db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Marker fixture — tables and seed already created at module level."""
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    """Fresh DB session per test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    """FastAPI test client with overridden DB dependency."""
    from app.main import app
    app.dependency_overrides[get_db] = override_get_db
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
