from bson import ObjectId

from app.core.exceptions import AppException
from app.core.http_status import HttpStatus
from app.core.security import hash_password
from app.infrastructure.logging import create_logger
from app.modules.users.repository import UserRepository

logger = create_logger(__name__)


async def list_users(db, search: str | None = None) -> list[dict]:
    repo = UserRepository(db)
    return await repo.list_users(search)


async def find_by_id(db, user_id: str) -> dict | None:
    repo = UserRepository(db)
    return await repo.find_by_id(user_id)


async def create_user(db, data: dict) -> dict:
    repo = UserRepository(db)
    email = data["email"].lower().strip()
    existing = await repo.find_by_email(email)
    if existing:
        raise AppException("User with this email already exists", HttpStatus.CONFLICT)

    document = {
        "name": data["name"].strip(),
        "email": email,
        "password": hash_password(data["password"]),
        "role": None,
        "isActive": data.get("isActive", True),
    }

    if data.get("role"):
        role_doc = await db["roles"].find_one({"name": data["role"]})
        if role_doc:
            document["role"] = role_doc["_id"]

    return await repo.create(document)


async def update_user(db, user_id: str, data: dict) -> dict:
    repo = UserRepository(db)
    user = (
        await repo.find_by_email(data.get("email", "")) if data.get("email") else None
    )
    if not user:
        try:
            user_doc = await db["users"].find_one({"_id": ObjectId(user_id)})
        except Exception:
            raise AppException("User not found", HttpStatus.NOT_FOUND)
        if not user_doc:
            raise AppException("User not found", HttpStatus.NOT_FOUND)
    else:
        user_doc = {
            "_id": ObjectId(user_id),
            **(await db["users"].find_one({"_id": ObjectId(user_id)}) or {}),
        }

    if not user_doc or "_id" not in user_doc:
        raise AppException("User not found", HttpStatus.NOT_FOUND)

    updates = {}

    if data.get("email") and data["email"].lower() != user_doc.get("email"):
        existing = await repo.find_by_email(data["email"].lower())
        if existing and str(existing.get("_id", "")) != user_id:
            raise AppException(
                "User with this email already exists", HttpStatus.CONFLICT
            )
        updates["email"] = data["email"].lower().strip()

    if data.get("password"):
        updates["password"] = hash_password(data["password"])

    if data.get("role"):
        role_doc = await db["roles"].find_one({"name": data["role"]})
        if role_doc:
            updates["role"] = role_doc["_id"]

    if data.get("name") is not None:
        updates["name"] = data["name"].strip()
    if data.get("email") is not None:
        updates["email"] = data["email"].lower().strip()
    if data.get("isActive") is not None:
        updates["isActive"] = data["isActive"]

    if updates:
        await repo.update(user_id, updates)

    return await repo.find_by_id(user_id)


async def delete_user(db, user_id: str):
    repo = UserRepository(db)
    deleted = await repo.delete(user_id)
    if not deleted:
        raise AppException("User not found", HttpStatus.NOT_FOUND)
