import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.infrastructure.mongo.client import get_db, init_db

settings.DB_NAME = "erp-fastapi-test"
settings.REDIS_URL = "memory://"


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _init_db():
    await init_db()


@pytest_asyncio.fixture(scope="function")
async def db():
    db_instance = get_db()
    return db_instance


@pytest_asyncio.fixture(scope="function")
async def client():
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def admin_token(db):
    await db["products"].delete_many({})
    await db["categories"].delete_many({})
    await db["sales"].delete_many({})
    await db["roles"].delete_many({})
    await db["users"].delete_many({})
    await db["roles"].insert_one({"name": "admin", "isSystem": True})
    role = await db["roles"].find_one({"name": "admin"})
    await db["users"].insert_one(
        {
            "name": "Admin",
            "email": "admin@test.com",
            "password": hash_password("admin123"),
            "role": role["_id"],
            "isActive": True,
        }
    )
    user = await db["users"].find_one({"email": "admin@test.com"})
    token = create_access_token({"id": str(user["_id"]), "role": str(role["_id"])})
    yield token
    await db["users"].delete_many({})
    await db["roles"].delete_many({})


@pytest_asyncio.fixture(scope="function")
async def employee_token(db):
    await db["products"].delete_many({})
    await db["categories"].delete_many({})
    await db["sales"].delete_many({})
    await db["roles"].delete_many({})
    await db["users"].delete_many({})
    await db["roles"].insert_one({"name": "employee", "isSystem": True})
    role = await db["roles"].find_one({"name": "employee"})
    await db["users"].insert_one(
        {
            "name": "Employee",
            "email": "employee@test.com",
            "password": hash_password("employee123"),
            "role": role["_id"],
            "isActive": True,
        }
    )
    user = await db["users"].find_one({"email": "employee@test.com"})
    token = create_access_token({"id": str(user["_id"]), "role": str(role["_id"])})
    yield token
    await db["users"].delete_many({})
    await db["roles"].delete_many({})
