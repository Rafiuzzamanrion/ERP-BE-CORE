import bcrypt
import pytest


@pytest.mark.asyncio
async def test_login_success(client, db):
    await db["roles"].insert_one({"name": "admin", "isSystem": True})
    role = await db["roles"].find_one({"name": "admin"})
    await db["users"].insert_one(
        {
            "name": "Test User",
            "email": "test@login.com",
            "password": bcrypt.hashpw(b"password123", bcrypt.gensalt(12)).decode(
                "utf-8"
            ),
            "role": role["_id"],
            "isActive": True,
        }
    )

    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@login.com",
            "password": "password123",
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "token" in data["data"]
    assert data["data"]["user"]["email"] == "test@login.com"


@pytest.mark.asyncio
async def test_login_wrong_password(client, db):
    await db["roles"].insert_one({"name": "admin", "isSystem": True})
    role = await db["roles"].find_one({"name": "admin"})
    await db["users"].insert_one(
        {
            "name": "Test User",
            "email": "wrong@login.com",
            "password": bcrypt.hashpw(b"correct123", bcrypt.gensalt(12)).decode(
                "utf-8"
            ),
            "role": role["_id"],
            "isActive": True,
        }
    )

    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrong@login.com",
            "password": "wrongpassword",
        },
    )

    assert resp.status_code == 401
    data = resp.json()
    assert data["success"] is False


@pytest.mark.asyncio
async def test_login_nonexistent_email(client):
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nobody@login.com",
            "password": "password123",
        },
    )

    assert resp.status_code == 401
    data = resp.json()
    assert data["success"] is False
