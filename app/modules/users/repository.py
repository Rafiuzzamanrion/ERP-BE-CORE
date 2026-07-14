import re

from bson import ObjectId

from app.infrastructure.logging import create_logger

logger = create_logger(__name__)


class UserRepository:
    def __init__(self, db):
        self.db = db

    def _serialize(self, user: dict) -> dict:
        role_val = user.get("role")
        if isinstance(role_val, dict):
            role_name = role_val.get("name")
        elif isinstance(role_val, str) and len(role_val) == 24:
            role_name = None
        else:
            role_name = role_val
        return {
            "_id": str(user["_id"]),
            "name": user.get("name", ""),
            "email": user.get("email", ""),
            "role": role_name,
            "isActive": user.get("isActive", True),
            "createdAt": user.get("createdAt").isoformat()
            if user.get("createdAt")
            else None,
            "updatedAt": user.get("updatedAt").isoformat()
            if user.get("updatedAt")
            else None,
        }

    async def find_by_email(self, email: str) -> dict | None:
        return await self.db["users"].find_one({"email": email})

    async def find_by_id(self, user_id: str) -> dict | None:
        try:
            pipeline = [
                {"$match": {"_id": ObjectId(user_id)}},
                {
                    "$lookup": {
                        "from": "roles",
                        "localField": "role",
                        "foreignField": "_id",
                        "as": "role",
                    }
                },
                {"$unwind": {"path": "$role", "preserveNullAndEmptyArrays": True}},
            ]
            cursor = await self.db["users"].aggregate(pipeline)
            users = await cursor.to_list(length=1)
            return self._serialize(users[0]) if users else None
        except Exception:
            return None

    async def list_users(self, search: str | None = None) -> list[dict]:
        filter_doc: dict = {}
        if search:
            escaped = re.escape(search)
            filter_doc["$or"] = [
                {"name": {"$regex": escaped, "$options": "i"}},
                {"email": {"$regex": escaped, "$options": "i"}},
            ]
        pipeline = [
            {"$match": filter_doc},
            {"$sort": {"createdAt": -1}},
            {
                "$lookup": {
                    "from": "roles",
                    "localField": "role",
                    "foreignField": "_id",
                    "as": "role",
                }
            },
            {"$unwind": {"path": "$role", "preserveNullAndEmptyArrays": True}},
        ]
        cursor = await self.db["users"].aggregate(pipeline)
        users = await cursor.to_list(length=None)
        return [self._serialize(u) for u in users]

    async def create(self, data: dict) -> dict:
        result = await self.db["users"].insert_one(data)
        return await self.find_by_id(str(result.inserted_id))

    async def update(self, user_id: str, updates: dict) -> dict:
        await self.db["users"].update_one({"_id": ObjectId(user_id)}, {"$set": updates})
        return await self.find_by_id(user_id)

    async def delete(self, user_id: str) -> bool:
        result = await self.db["users"].delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0
