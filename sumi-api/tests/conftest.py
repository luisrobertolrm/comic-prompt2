import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import Session, sessionmaker

from prompt_clinica.main import app
from prompt_clinica.database import get_db

# SQLite em memória para testes (sem precisar de PostgreSQL)
_TEST_URL = "sqlite:///:memory:"

_test_engine = create_engine(
    _TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSession = sessionmaker(bind=_test_engine, autocommit=False, autoflush=False)


def _override_get_db() -> Session:  # type: ignore[override]
    db: Session = _TestSession()
    try:
        yield db  # type: ignore[misc]
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def _create_tables() -> None:
    from base import Base  # models/base.py
    import all_models  # noqa: F401  models/all_models.py
    Base.metadata.create_all(bind=_test_engine)


@pytest.fixture()
def client() -> TestClient:
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def db() -> Session:  # type: ignore[type-arg]
    session: Session = _TestSession()
    try:
        yield session  # type: ignore[misc]
    finally:
        session.rollback()
        session.close()
