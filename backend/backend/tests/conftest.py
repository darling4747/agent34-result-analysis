"""Test configuration and shared fixtures."""
import io
import os
import pytest
import pandas as pd
from unittest.mock import patch

# Set env vars BEFORE any app imports so lru_cache picks them up
os.environ["DATABASE_URL"] = "sqlite:///./test_result_analysis.db"

# Remove stale test DB at import time (before engine is created)
_TEST_DB_PATH = "./test_result_analysis.db"
for _suffix in ["", "-wal", "-shm"]:
    try:
        os.remove(_TEST_DB_PATH + _suffix)
    except (FileNotFoundError, PermissionError):
        pass

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Clear the lru_cache so settings re-read the new env var
from app.config import get_settings
get_settings.cache_clear()

from app.database import Base, get_db

TEST_DB_URL = "sqlite:///./test_result_analysis.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(setup_database):
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    from app.main import app
    app.dependency_overrides[get_db] = override_get_db
    # Patch init_db so lifespan doesn't re-run create_all on the already-setup test DB
    with patch("app.main.init_db"):
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_excel_bytes():
    """Return bytes of a minimal valid Excel result file."""
    data = {
        "roll_number": ["22CS001", "22CS002", "22CS003"],
        "student_name": ["Alice", "Bob", "Charlie"],
        "programme": ["B.Tech", "B.Tech", "B.Tech"],
        "department": ["CSE", "CSE", "CSE"],
        "batch": ["2022", "2022", "2022"],
        "section": ["A", "A", "A"],
        "course_code": ["CS601", "CS601", "CS601"],
        "course_name": ["Compiler Design", "Compiler Design", "Compiler Design"],
        "faculty": ["Dr. R. Kumar", "Dr. R. Kumar", "Dr. R. Kumar"],
        "semester": [6, 6, 6],
        "academic_year": ["2025-26", "2025-26", "2025-26"],
        "internal_marks": [22, 18, 25],
        "external_marks": [50, 35, 60],
        "total_marks": [72, 53, 85],
        "grade": ["A", "C", "O"],
        "grade_point": [8, 5, 10],
        "result_status": ["PASS", "PASS", "PASS"],
    }
    df = pd.DataFrame(data)
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    return buf.read()


@pytest.fixture
def sample_excel_with_failures():
    """Excel bytes with some failing rows."""
    data = {
        "roll_number": [f"22CS{i:03d}" for i in range(1, 21)],
        "student_name": [f"Student {i}" for i in range(1, 21)],
        "programme": ["B.Tech"] * 20,
        "department": ["CSE"] * 20,
        "batch": ["2022"] * 20,
        "section": (["A"] * 5 + ["B"] * 5 + ["A"] * 5 + ["B"] * 5),
        "course_code": (["CS601"] * 10 + ["CS606"] * 10),
        "course_name": (["Compiler Design"] * 10 + ["Operating Systems"] * 10),
        "faculty": (["Dr. R. Kumar"] * 10 + ["Dr. M. Sharma"] * 10),
        "semester": [6] * 20,
        "academic_year": ["2025-26"] * 20,
        "internal_marks": [22, 18, 25, 15, 20, 10, 8, 12, 15, 19,
                           22, 18, 25, 15, 20, 10, 8, 12, 15, 19],
        "external_marks": [50, 35, 60, 25, 40, 15, 10, 20, 30, 38,
                           50, 35, 60, 25, 40, 15, 10, 20, 30, 38],
        "total_marks": [72, 53, 85, 40, 60, 25, 18, 32, 45, 57,
                        72, 53, 85, 40, 60, 25, 18, 32, 45, 57],
        "grade": ["A", "C", "O", "C", "B", "F", "F", "F", "P", "B",
                  "A", "C", "O", "C", "B", "F", "F", "F", "P", "B"],
        "grade_point": [8, 5, 10, 5, 6, 0, 0, 0, 4, 6,
                        8, 5, 10, 5, 6, 0, 0, 0, 4, 6],
        "result_status": ["PASS", "PASS", "PASS", "PASS", "PASS", "FAIL", "FAIL", "FAIL", "PASS", "PASS",
                          "PASS", "PASS", "PASS", "PASS", "PASS", "FAIL", "FAIL", "FAIL", "PASS", "PASS"],
    }
    df = pd.DataFrame(data)
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# Authenticated client fixtures (required after RBAC was added to routes)
# ---------------------------------------------------------------------------

def _seed_admin(db_session):
    from app.services.auth_service import AuthService
    from app.security.password import hash_password
    from app.models import Role, User
    from app.config import get_settings
    svc = AuthService(db_session, get_settings())
    svc.seed_roles_and_permissions()
    role = db_session.query(Role).filter_by(name="PLATFORM_ADMIN").first()
    email = "fixture_admin@test.com"
    u = db_session.query(User).filter_by(email=email).first()
    if not u:
        u = User(
            email=email, full_name="Fixture Admin", role_id=role.id,
            is_active=True, password_hash=hash_password("FixturePass99!X"),
            must_change_password=False, mfa_enabled=False,
        )
        db_session.add(u)
    else:
        u.mfa_enabled = False
        u.mfa_secret_encrypted = None
        u.mfa_pending_secret_encrypted = None
    db_session.commit()
    return email


@pytest.fixture
def auth_client(client, db_session):
    email = _seed_admin(db_session)
    resp = client.post("/api/auth/login", json={"email": email, "password": "FixturePass99!X"})
    assert resp.status_code == 200, f"Fixture login failed: {resp.json()}"
    token = resp.json()["data"]["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
