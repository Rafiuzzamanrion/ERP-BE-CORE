from bson import ObjectId

from app.infrastructure.logging import create_logger

logger = create_logger(__name__)


class AuthRepository:
    def __init__(self, db):
        self.db = db

    async def find_user_by_email(self, email: str) -> dict | None:
        return await self.db["users"].find_one({"email": email.lower().strip()})

    async def find_user_by_id(self, user_id: str) -> dict | None:
        try:
            return await self.db["users"].find_one({"_id": ObjectId(user_id)})
        except Exception:
            return None

    async def resolve_role_name(self, role_id) -> str:
        if not role_id:
            return "employee"
        try:
            rid = str(role_id) if isinstance(role_id, ObjectId) else str(role_id)
            role = await self.db["roles"].find_one({"_id": ObjectId(rid)}, {"name": 1})
            return role["name"] if role else "employee"
        except Exception:
            return "employee"
