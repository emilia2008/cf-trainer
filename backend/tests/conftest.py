import os

# Tests must never touch the development database. Set before any app module is imported.
os.environ["DATABASE_URL"] = "sqlite://"

import pytest  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app import models  # noqa: E402,F401  (registers tables with Base)
from app.db import Base, make_engine  # noqa: E402


@pytest.fixture
def engine():
    """In-memory SQLite by default. Set TEST_DATABASE_URL to run against PostgreSQL (CI does)."""
    url = os.environ.get("TEST_DATABASE_URL")
    engine = make_engine(url or "sqlite://")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def session(engine):
    with Session(engine, expire_on_commit=False) as session:
        yield session
