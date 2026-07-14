import re

from bson import ObjectId

from app.infrastructure.logging import create_logger

logger = create_logger(__name__)


def _serialize(doc: dict) -> dict:
    if doc is None:
        return None
    result = {k: v for k, v in doc.items() if k != "__v"}
    result["_id"] = str(doc["_id"])
    if "createdBy" in result and isinstance(result["createdBy"], ObjectId):
        result["createdBy"] = str(result["createdBy"])
    return result


class ProductRepository:
    def __init__(self, db):
        self.db = db

    async def find_by_sku(self, sku: str) -> dict | None:
        return await self.db["products"].find_one({"sku": sku})

    async def find_by_id(self, product_id: str) -> dict | None:
        try:
            product = await self.db["products"].find_one({"_id": ObjectId(product_id)})
            return _serialize(product)
        except Exception:
            return None

    async def list_paginated(
        self, search: str | None, category: str | None, page: int, limit: int, sort: str
    ) -> tuple[list[dict], dict]:
        filter_doc: dict = {}
        if search and search.strip():
            escaped = re.escape(search.strip())
            filter_doc["$or"] = [
                {"name": {"$regex": escaped, "$options": "i"}},
                {"sku": {"$regex": escaped, "$options": "i"}},
                {"category": {"$regex": escaped, "$options": "i"}},
            ]
        if category and category.strip():
            filter_doc["category"] = category.strip().lower()
        sort_field = sort.lstrip("-")
        sort_order = -1 if sort.startswith("-") else 1
        total = await self.db["products"].count_documents(filter_doc)
        products = (
            await self.db["products"]
            .find(
                filter_doc,
                {
                    "name": 1,
                    "sku": 1,
                    "category": 1,
                    "sellingPrice": 1,
                    "stockQuantity": 1,
                    "imageUrl": 1,
                    "createdAt": 1,
                    "purchasePrice": 1,
                    "imagePublicId": 1,
                    "createdBy": 1,
                },
            )
            .sort(sort_field, sort_order)
            .skip((page - 1) * limit)
            .limit(limit)
            .to_list(length=limit)
        )
        total_pages = max(1, (total + limit - 1) // limit) if total > 0 else 1
        meta = {"page": page, "limit": limit, "total": total, "totalPages": total_pages}
        return [_serialize(p) for p in products], meta

    async def create(self, data: dict) -> dict:
        result = await self.db["products"].insert_one(data)
        product = await self.db["products"].find_one({"_id": result.inserted_id})
        return _serialize(product)

    async def update(self, product_id: str, updates: dict) -> dict:
        await self.db["products"].update_one(
            {"_id": ObjectId(product_id)}, {"$set": updates}
        )
        return await self.find_by_id(product_id)

    async def delete(self, product_id: str) -> dict | None:
        product = await self.db["products"].find_one({"_id": ObjectId(product_id)})
        if product:
            await self.db["products"].delete_one({"_id": ObjectId(product_id)})
            return _serialize(product)
        return None
