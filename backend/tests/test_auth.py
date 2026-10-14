import pytest
from datetime import timedelta
from app.core.security import hash_password, verify_password, create_access_token, decode_token


def test_password_hashing():
    pwd = "SecretPassword123!"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_generation_and_decode():
    payload = {"sub": "user-123", "role": "Admin", "type": "access"}
    token = create_access_token(payload, expires_delta=timedelta(minutes=15))
    decoded = decode_token(token)
    assert decoded is not None
    assert decoded["sub"] == "user-123"
    assert decoded["role"] == "Admin"
    assert decoded["type"] == "access"


def test_jwt_expired_token():
    payload = {"sub": "user-123", "role": "Admin", "type": "access"}
    token = create_access_token(payload, expires_delta=timedelta(seconds=-1))
    decoded = decode_token(token)
    assert decoded is None


def test_login_success(client, test_admin_user):
    resp = client.post("/api/v1/auth/login", json={
        "email": test_admin_user.email,
        "password": "AdminPass123!"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["role"] == "Admin"
    assert data["email"] == test_admin_user.email


def test_login_invalid_password(client, test_admin_user):
    resp = client.post("/api/v1/auth/login", json={
        "email": test_admin_user.email,
        "password": "IncorrectPassword"
    })
    assert resp.status_code == 401


def test_login_nonexistent_user(client):
    resp = client.post("/api/v1/auth/login", json={
        "email": "ghost@kestral.ai",
        "password": "AnyPassword123!"
    })
    assert resp.status_code == 401


def test_get_current_user_profile(client, admin_headers, test_admin_user):
    resp = client.get("/api/v1/auth/me", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == test_admin_user.email
    assert data["name"] == test_admin_user.name


def test_unauthorized_access_without_token(client):
    resp = client.get("/api/v1/users")
    assert resp.status_code == 401


def test_role_based_access_admin_only(client, officer_headers, admin_headers):
    # Officer tries to create a new user (admin required)
    resp = client.post("/api/v1/users", headers=officer_headers, json={
        "name": "New User",
        "email": "newuser@kestral.ai",
        "password": "Password123!",
        "role": "Officer"
    })
    assert resp.status_code == 403

    # Admin successfully creates new user
    resp_admin = client.post("/api/v1/users", headers=admin_headers, json={
        "name": "New User",
        "email": "newuser@kestral.ai",
        "password": "Password123!",
        "role": "Officer"
    })
    assert resp_admin.status_code == 201
    assert resp_admin.json()["email"] == "newuser@kestral.ai"
