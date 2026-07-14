from bson import ObjectId

from app.core.deps import clear_permission_cache
from app.infrastructure.logging import create_logger

logger = create_logger(__name__)


def _serialize(doc: dict) -> dict:
    if doc is None:
        return None
    result = {k: v for k, v in doc.items() if k != "__v"}
    result["_id"] = str(doc["_id"])
    if "permissions" in result and isinstance(result["permissions"], list):
        result["permissions"] = [
            {**p, "_id": str(p["_id"])} if isinstance(p, dict) else str(p)
            for p in result["permissions"]
        ]
    result.pop("id", None)
    return result


class RoleRepository:
    def __init__(self, db):
        self.db = db

    async def find_by_name(self, name: str) -> dict | None:
        return await self.db["roles"].find_one({"name": name})

    async def find_by_id(self, role_id: str) -> dict:
        try:
            pipeline = [
                {"$match": {"_id": ObjectId(role_id)}},
                {
                    "$lookup": {
                        "from": "permissions",
                        "localField": "permissions",
                        "foreignField": "_id",
                        "as": "permissions",
                    }
                },
            ]
            cursor = await self.db["roles"].aggregate(pipeline)
            roles = await cursor.to_list(length=1)
            if not roles:
                return None
            return _serialize(roles[0])
        except Exception:
            return None

    async def list_all(self) -> list[dict]:
        pipeline = [
            {
                "$lookup": {
                    "from": "permissions",
                    "localField": "permissions",
                    "foreignField": "_id",
                    "as": "permissions",
                }
            }
        ]
        cursor = await self.db["roles"].aggregate(pipeline)
        roles = await cursor.to_list(length=None)
        return [_serialize(r) for r in roles]

    async def create(self, data: dict) -> dict:
        result = await self.db["roles"].insert_one(data)
        return _serialize(await self.db["roles"].find_one({"_id": result.inserted_id}))

    async def update(self, role_id: str, updates: dict) -> dict:
        await self.db["roles"].update_one({"_id": ObjectId(role_id)}, {"$set": updates})
        await clear_permission_cache(role_id)
        return await self.find_by_id(role_id)

    async def delete(self, role_id: str) -> dict:
        role = await self.db["roles"].find_one({"_id": ObjectId(role_id)})
        if role:
            await self.db["roles"].delete_one({"_id": ObjectId(role_id)})
            await clear_permission_cache(role_id)
            return _serialize(role)
        return None


class PermissionRepository:
    def __init__(self, db):
        self.db = db

    async def find_by_key(self, key: str) -> dict | None:
        return await self.db["permissions"].find_one({"key": key})

    async def find_by_id(self, perm_id: str) -> dict | None:
        try:
            perm = await self.db["permissions"].find_one({"_id": ObjectId(perm_id)})
            return _serialize(perm)
        except Exception:
            return None

    async def list_all(self) -> list[dict]:
        perms = await self.db["permissions"].find().to_list(length=None)
        return [_serialize(p) for p in perms]

    async def create(self, data: dict) -> dict:
        doc = {"key": data["key"].strip(), "description": data["description"].strip()}
        result = await self.db["permissions"].insert_one(doc)
        perm = await self.db["permissions"].find_one({"_id": result.inserted_id})
        return _serialize(perm)

    async def update(self, perm_id: str, updates: dict) -> dict:
        await self.db["permissions"].update_one(
            {"_id": ObjectId(perm_id)}, {"$set": updates}
        )
        return await self.find_by_id(perm_id)

    async def delete(self, perm_id: str) -> dict:
        perm = await self.db["permissions"].find_one({"_id": ObjectId(perm_id)})
        if perm:
            await self.db["permissions"].delete_one({"_id": ObjectId(perm_id)})
            return _serialize(perm)
        return None
