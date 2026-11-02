
import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models import *  # noqa: F401, F403
from app.api.deps import get_database_session
from app.main import app


@pytest.fixture(scope="session")
def test_engine():
    database_url = os.getenv("TEST_DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "TEST_DATABASE_URL must be set before running tests."
        )

    if "peoplesphere_test" not in database_url:
        raise RuntimeError(
            "Tests are allowed to run only against peoplesphere_test."
        )

    engine = create_engine(database_url, pool_pre_ping=True)

    if engine.url.database != "peoplesphere_test":
        raise RuntimeError("Unexpected test database.")

    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()

    TestingSessionLocal = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    from fastapi.testclient import TestClient

    def override_get_database_session():
        yield db_session

    app.dependency_overrides[get_database_session] = (
        override_get_database_session
    )

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_database_session, None)
