# tests/integration/conftest.py
"""
Database fixtures for integration tests.

These fixtures connect to a real PostgreSQL database (the one provided by the
GitHub Actions ``postgres`` service, or a local instance). If no database is
reachable, the DB-backed tests are skipped rather than failing, so the rest of
the suite still runs locally without Postgres.

Connection string comes from the ``DATABASE_URL`` environment variable.
"""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from app.database import Base
# Import models so they register with Base.metadata before create_all().
from app.models.user import User  # noqa: F401
from app.models.calculation import Calculation  # noqa: F401

DEFAULT_DATABASE_URL = "postgresql://user:password@localhost:5432/myappdb"


@pytest.fixture(scope="session")
def db_engine():
    """
    Session-scoped engine. Creates all tables up front and drops them at the
    end. Skips the DB tests entirely if the database cannot be reached.
    """
    url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    engine = create_engine(url)
    try:
        conn = engine.connect()
    except OperationalError as exc:
        pytest.skip(f"Database not reachable at {url}: {exc}")
    conn.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    Function-scoped session wrapped in a transaction that is rolled back after
    each test, keeping tests isolated from one another.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        # A failed commit inside a test may already have rolled the
        # transaction back; only roll back if it is still active.
        if transaction.is_active:
            transaction.rollback()
        connection.close()
