from datetime import UTC, datetime
from typing import Generic, TypeVar

from bson import ObjectId
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.results import InsertOneResult

from app.infrastructure.logging import create_logger

logger = create_logger(__name__)

T = TypeVar("T")


class PaginationMeta:
    def __init__(self, page: int, limit: int, total: int):
        self.page = page
        self.limit = limit
        self.total = total

    @property
    def total_pages(self) -> int:
        return (
            max(1, (self.total + self.limit - 1) // self.limit) if self.total > 0 else 1
        )

    def to_dict(self) -> dict:
        return {
            "page": self.page,
            "limit": self.limit,
            "total": self.total,
            "totalPages": self.total_pages,
        }


class BaseRepository(Generic[T]):
    def __init__(self, db: AsyncDatabase, collection_name: str):
        self.collection: AsyncCollection = db[collection_name]
        self._collection_name = collection_name

    def _encode(self, doc: dict) -> dict:
        return doc

    def _decode(self, doc: dict | None) -> dict | None:
        if doc is None:
            return None
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return doc

    def _decode_many(self, docs: list[dict]) -> list[dict]:
        return [self._decode(d) for d in docs]

    def _oid(self, id_str: str) -> ObjectId:
        return ObjectId(id_str)

    def _now(self) -> datetime:
        return datetime.now(UTC)

    async def find_by_id(self, id_str: str) -> dict | None:
        try:
            doc = await self.collection.find_one({"_id": self._oid(id_str)})
            return self._decode(doc)
        except Exception:
            return None

    async def find_one(self, filter_dict: dict) -> dict | None:
        doc = await self.collection.find_one(filter_dict)
        return self._decode(doc)

    async def find_many(
        self,
        filter_dict: dict | None = None,
        sort: list[tuple[str, int]] | None = None,
        skip: int = 0,
        limit: int = 100,
        projection: dict | None = None,
    ) -> list[dict]:
        filter_dict = filter_dict or {}
        cursor = self.collection.find(filter_dict, projection=projection)
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        docs = await cursor.to_list(length=limit)
        return self._decode_many(docs)

    async def paginate(
        self,
        filter_dict: dict | None = None,
        sort: str = "createdAt",
        sort_order: int = -1,
        page: int = 1,
        limit: int = 10,
        projection: dict | None = None,
    ) -> tuple[list[dict], PaginationMeta]:
        filter_dict = filter_dict or {}
        total = await self.collection.count_documents(filter_dict)
        cursor = (
            self.collection.find(filter_dict, projection=projection)
            .sort(sort, sort_order)
            .skip((page - 1) * limit)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        meta = PaginationMeta(page=page, limit=limit, total=total)
        return self._decode_many(docs), meta

    async def insert_one_doc(self, document: dict) -> str:
        now = self._now()
        document.setdefault("createdAt", now)
        document.setdefault("updatedAt", now)
        result: InsertOneResult = await self.collection.insert_one(document)
        return str(result.inserted_id)

    async def update_one_doc(self, id_str: str, updates: dict) -> bool:
        updates.setdefault("updatedAt", self._now())
        result = await self.collection.update_one(
            {"_id": self._oid(id_str)},
            {"$set": updates},
        )
        return result.modified_count > 0 or result.matched_count > 0

    async def delete_one_doc(self, id_str: str) -> bool:
        result = await self.collection.delete_one({"_id": self._oid(id_str)})
        return result.deleted_count > 0

    async def count(self, filter_dict: dict | None = None) -> int:
        return await self.collection.count_documents(filter_dict or {})

    async def exists(self, filter_dict: dict) -> bool:
        count = await self.collection.count_documents(filter_dict, limit=1)
        return count > 0

    async def aggregate(self, pipeline: list[dict]) -> list[dict]:
        cursor = await self.collection.aggregate(pipeline)
        docs = await cursor.to_list(length=None)
        return docs

    async def aggregate_one(self, pipeline: list[dict]) -> dict | None:
        pipeline.append({"$limit": 1})
        docs = await self.aggregate(pipeline)
        return docs[0] if docs else None

    async def aggregate_paginated(
        self,
        pipeline: list[dict],
        page: int = 1,
        limit: int = 10,
    ) -> tuple[list[dict], PaginationMeta]:
        facet_pipeline = list(pipeline)
        facet_pipeline.append(
            {
                "$facet": {
                    "items": [{"$skip": (page - 1) * limit}, {"$limit": limit}],
                    "total": [{"$count": "count"}],
                }
            }
        )
        results = await self.aggregate(facet_pipeline)
        result = results[0] if results else {"items": [], "total": [{"count": 0}]}
        items = result.get("items", [])
        total = (
            result.get("total", [{}])[0].get("count", 0) if result.get("total") else 0
        )
        meta = PaginationMeta(page=page, limit=limit, total=total)
        return items, meta

    async def bulk_write_ops(self, operations: list) -> dict:
        result = await self.collection.bulk_write(operations)
        return {
            "matched": result.matched_count,
            "modified": result.modified_count,
            "inserted": result.inserted_count,
            "deleted": result.deleted_count,
        }

    @staticmethod
    def lookup(
        from_collection: str, local_field: str, foreign_field: str, as_field: str
    ) -> dict:
        return {
            "$lookup": {
                "from": from_collection,
                "localField": local_field,
                "foreignField": foreign_field,
                "as": as_field,
            }
        }

    @staticmethod
    def unwind(path: str, preserve_null: bool = True) -> dict:
        return {"$unwind": {"path": path, "preserveNullAndEmptyArrays": preserve_null}}

    @staticmethod
    def project(fields: dict) -> dict:
        return {"$project": fields}

    @staticmethod
    def match(filter_dict: dict) -> dict:
        return {"$match": filter_dict}

    @staticmethod
    def sort_by(field: str, order: int = -1) -> dict:
        return {"$sort": {field: order}}

    @staticmethod
    def add_fields(fields: dict) -> dict:
        return {"$addFields": fields}

    @staticmethod
    def group(group_by: dict) -> dict:
        return {"$group": group_by}
