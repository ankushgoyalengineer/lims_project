# tests/conftest.py
import os
import sys
import pathlib

# 1) test runner env must be set before importing app modules
os.environ.setdefault("ENV", "testing")

# ensure repo root on sys.path so `import app` works
ROOT = str(pathlib.Path(__file__).resolve().parents[1])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# 2) test DB path and env - set BEFORE importing app modules that read config
TEST_DB = os.path.join(ROOT, "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"

# remove stale test DB file so tests start clean
try:
    os.remove(TEST_DB)
except FileNotFoundError:
    pass

# 3) disable limiter BEFORE app import so middleware is not installed
from app.limiter import limiter as _limiter
_limiter.enabled = False

# now import app modules
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.db import Base, get_db, engine as app_engine
from app.main import app
from app.models.user import User
from app.core.security import hash_password

# ensure the running app instance has the disabled limiter attached
app.state.limiter = _limiter

# Create tables using app's engine (based on DATABASE_URL above)
Base.metadata.create_all(bind=app_engine)


import pytest  # keep pytest import near fixtures (optional ordering)

@pytest.fixture(scope="session")
def engine():
    yield app_engine


@pytest.fixture()
def db_session(engine):
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def client(db_session, monkeypatch):
    # override get_db to yield the same db_session used by tests
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    # override get_current_user to return the test user present in db_session
    def _get_test_current_user():
        return db_session.query(User).filter(User.email == "test@example.com").first()

    # ensure the app uses the test DB for any further imports
    monkeypatch.setenv("DATABASE_URL", os.environ["DATABASE_URL"])
    app.dependency_overrides[get_db] = _get_test_db

    # import dependency target here to avoid circular early import issues
    try:
        from app.deps import get_current_user
        app.dependency_overrides[get_current_user] = _get_test_current_user
    except Exception:
        pass

    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clear_tables_and_seed_user(db_session):
    # truncate all tables before every test, then insert a stable test user
    for tbl in reversed(Base.metadata.sorted_tables):
        db_session.execute(tbl.delete())
    db_session.commit()

    # create a test user that routes will accept as authenticated user
    test_user = User(
        email="test@example.com",
        hashed_password=hash_password("abc12345"),
        full_name="Test User",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(test_user)
    db_session.commit()

    yield
