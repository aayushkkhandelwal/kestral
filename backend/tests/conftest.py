import os
import sys
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

# Ensure backend root is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.database.base import Base
from app.database.session import get_db
from app.models.user import User
from app.core.security import hash_password, create_access_token
from app.core.permissions import UserRole
import main

# Test SQLite in-memory database with StaticPool
TEST_DB_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    main.app.dependency_overrides[get_db] = override_get_db
    with TestClient(main.app) as c:
        yield c
    main.app.dependency_overrides.clear()


@pytest.fixture
def test_admin_user(db) -> User:
    user = User(
        name="Admin Tester",
        email="admintester@kestral.ai",
        password_hash=hash_password("AdminPass123!"),
        role="Admin",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_investigator_user(db) -> User:
    user = User(
        name="Investigator Tester",
        email="investigator@kestral.ai",
        password_hash=hash_password("Investigator123!"),
        role="Investigator",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_officer_user(db) -> User:
    user = User(
        name="Officer Tester",
        email="officer@kestral.ai",
        password_hash=hash_password("OfficerPass123!"),
        role="Officer",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_headers(test_admin_user) -> dict:
    payload = {
        "sub": str(test_admin_user.id),
        "email": test_admin_user.email,
        "role": test_admin_user.role,
        "name": test_admin_user.name,
        "type": "access"
    }
    token = create_access_token(payload)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def investigator_headers(test_investigator_user) -> dict:
    payload = {
        "sub": str(test_investigator_user.id),
        "email": test_investigator_user.email,
        "role": test_investigator_user.role,
        "name": test_investigator_user.name,
        "type": "access"
    }
    token = create_access_token(payload)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def officer_headers(test_officer_user) -> dict:
    payload = {
        "sub": str(test_officer_user.id),
        "email": test_officer_user.email,
        "role": test_officer_user.role,
        "name": test_officer_user.name,
        "type": "access"
    }
    token = create_access_token(payload)
    return {"Authorization": f"Bearer {token}"}
