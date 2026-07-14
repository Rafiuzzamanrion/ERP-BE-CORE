import re

from bson import ObjectId

from app.infrastructure.logging import create_logger

logger = create_logger(__name__)


def _serialize(doc: dict) -> dict:
    return {**doc, "_id": str(doc["_id"])} if doc else None


class CategoryRepository:
    def __init__(self, db):
        self.db = db

    async def find_by_name(self, name: str) -> dict | None:
        return await self.db["categories"].find_one({"name": name})

    async def find_by_id(self, category_id: str) -> dict | None:
        try:
            category = await self.db["categories"].find_one(
                {"_id": ObjectId(category_id)}
            )
            return _serialize(category)
        except Exception:
            return None

    async def list_paginated(
        self, search: str | None, page: int, limit: int, sort: str
    ) -> tuple[list[dict], dict]:
        sort_field = sort.lstrip("-")
        sort_order = -1 if sort.startswith("-") else 1
        filter_doc: dict = {}
        if search and search.strip():
            escaped = re.escape(search.strip())
            filter_doc["$or"] = [
                {"name": {"$regex": escaped, "$options": "i"}},
                {"description": {"$regex": escaped, "$options": "i"}},
            ]
        total = await self.db["categories"].count_documents(filter_doc)
        categories = (
            await self.db["categories"]
            .find(filter_doc)
            .sort(sort_field, sort_order)
            .skip((page - 1) * limit)
            .limit(limit)
            .to_list(length=limit)
        )
        total_pages = max(1, (total + limit - 1) // limit) if total > 0 else 1
        meta = {"page": page, "limit": limit, "total": total, "totalPages": total_pages}
        return [_serialize(c) for c in categories], meta

    async def create(self, data: dict) -> dict:
        result = await self.db["categories"].insert_one(data)
        category = await self.db["categories"].find_one({"_id": result.inserted_id})
        return _serialize(category)

    async def update(self, category_id: str, updates: dict) -> dict:
        await self.db["categories"].update_one(
            {"_id": ObjectId(category_id)}, {"$set": updates}
        )
        return await self.find_by_id(category_id)

    async def delete(self, category_id: str) -> dict | None:
        category = await self.db["categories"].find_one({"_id": ObjectId(category_id)})
        if category:
            await self.db["categories"].delete_one({"_id": ObjectId(category_id)})
            return _serialize(category)
        return None

    async def exists(self, name: str) -> bool:
        doc = await self.db["categories"].find_one(
            {"name": name.lower().strip()}, {"_id": 1}
        )
        return doc is not None

    async def count_products_using(self, name: str) -> int:
        return await self.db["products"].count_documents({"category": name})
