import re

from bson import ObjectId
from pymongo import UpdateOne

from app.core.exceptions import AppException
from app.core.http_status import HttpStatus
from app.infrastructure.logging import create_logger

logger = create_logger(__name__)


def _serialize(doc: dict) -> dict:
    if doc is None:
        return None
    result = {k: v for k, v in doc.items() if k != "__v"}
    result["_id"] = str(doc.pop("_id", doc.get("_id", "")))
    if "soldBy" in result:
        if isinstance(result["soldBy"], dict):
            result["soldBy"]["_id"] = str(result["soldBy"].get("_id", ""))
        elif isinstance(result["soldBy"], ObjectId):
            result["soldBy"] = str(result["soldBy"])
    if "items" in result:
        for item in result["items"]:
            if "product" in item:
                if isinstance(item["product"], dict):
                    item["product"]["_id"] = str(item["product"].get("_id", ""))
                elif isinstance(item["product"], ObjectId):
                    item["product"] = str(item["product"])
            if "_id" in item:
                item["_id"] = str(item.pop("_id"))
    return result


class SaleRepository:
    def __init__(self, db, sio=None):
        self.db = db
        self.sio = sio

    async def create_transaction(self, data: dict, user_id: str) -> dict:
        try:
            product_ids = [ObjectId(item["productId"]) for item in data["items"]]
            products_cursor = self.db["products"].find({"_id": {"$in": product_ids}})
            products = await products_cursor.to_list(length=None)
            product_map = {str(p["_id"]): p for p in products}
            items_with_details = []
            grand_total = 0.0
            low_stock_products = []
            bulk_ops = []

            for item in data["items"]:
                product = product_map.get(item["productId"])
                if not product:
                    raise AppException(
                        f"Product with ID {item['productId']} not found",
                        HttpStatus.NOT_FOUND,
                    )
                if product["stockQuantity"] < item["quantity"]:
                    raise AppException(
                        f"Insufficient stock for {product['name']}",
                        HttpStatus.BAD_REQUEST,
                    )
                unit_price = product["sellingPrice"]
                subtotal = unit_price * item["quantity"]
                new_stock = product["stockQuantity"] - item["quantity"]
                bulk_ops.append(
                    UpdateOne(
                        {"_id": product["_id"]},
                        {"$inc": {"stockQuantity": -item["quantity"]}},
                    )
                )
                items_with_details.append(
                    {
                        "product": product["_id"],
                        "productName": product["name"],
                        "quantity": item["quantity"],
                        "unitPrice": unit_price,
                        "subtotal": subtotal,
                    }
                )
                grand_total += subtotal
                if new_stock < 5:
                    low_stock_products.append(
                        {
                            "productId": str(product["_id"]),
                            "name": product["name"],
                            "sku": product["sku"],
                            "stockQuantity": new_stock,
                        }
                    )

            if bulk_ops:
                await self.db["products"].bulk_write(bulk_ops)

            sale_doc = {
                "items": items_with_details,
                "grandTotal": round(grand_total, 2),
                "soldBy": ObjectId(user_id),
            }
            result = await self.db["sales"].insert_one(sale_doc)

            for low_stock in low_stock_products:
                if self.sio:
                    await self.sio.emit("stock:low", low_stock)

            return await self._populate(result.inserted_id)
        except AppException:
            raise
        except Exception as e:
            logger.error("sale_transaction_failed", error=str(e))
            raise AppException("Failed to create sale", HttpStatus.INTERNAL_SERVER_ERROR)

    async def _populate(self, sale_id) -> dict:
        pipeline = [
            {"$match": {"_id": sale_id}},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "soldBy",
                    "foreignField": "_id",
                    "pipeline": [{"$project": {"name": 1, "email": 1}}],
                    "as": "soldBy",
                }
            },
            {"$unwind": {"path": "$soldBy", "preserveNullAndEmptyArrays": True}},
            {
                "$lookup": {
                    "from": "products",
                    "localField": "items.product",
                    "foreignField": "_id",
                    "pipeline": [
                        {
                            "$project": {
                                "name": 1,
                                "sku": 1,
                                "sellingPrice": 1,
                                "imageUrl": 1,
                                "stockQuantity": 1,
                                "category": 1,
                            }
                        }
                    ],
                    "as": "_productDetails",
                }
            },
        ]
        cursor = await self.db["sales"].aggregate(pipeline)
        sales = await cursor.to_list(length=1)
        if not sales:
            raise AppException(
                "Sale not found after creation", HttpStatus.INTERNAL_SERVER_ERROR
            )
        sale = sales[0]
        product_map = {str(p["_id"]): p for p in sale.pop("_productDetails", [])}
        for item in sale.get("items", []):
            pid = (
                str(item["product"])
                if isinstance(item["product"], ObjectId)
                else item["product"]
            )
            item["product"] = product_map.get(pid, item["product"])
        return _serialize(sale)

    async def list_paginated(
        self, search: str | None, page: int, limit: int, sort: str
    ) -> tuple[list[dict], dict]:
        sort_field = sort.lstrip("-")
        sort_order = -1 if sort.startswith("-") else 1
        pipeline = []
        if search and search.strip():
            escaped = re.escape(search.strip())
            pipeline.append(
                {"$match": {"items.productName": {"$regex": escaped, "$options": "i"}}}
            )
        pipeline.extend(
            [
                {"$sort": {sort_field: sort_order}},
                {
                    "$lookup": {
                        "from": "users",
                        "localField": "soldBy",
                        "foreignField": "_id",
                        "pipeline": [{"$project": {"name": 1, "email": 1}}],
                        "as": "soldBy",
                    }
                },
                {"$unwind": {"path": "$soldBy", "preserveNullAndEmptyArrays": True}},
                {
                    "$facet": {
                        "items": [{"$skip": (page - 1) * limit}, {"$limit": limit}],
                        "total": [{"$count": "count"}],
                    }
                },
            ]
        )
        cursor = await self.db["sales"].aggregate(pipeline)
        results = await cursor.to_list(length=1)
        result = results[0] if results else {"items": [], "total": [{"count": 0}]}
        items = result.get("items", [])
        total = next((t["count"] for t in result.get("total", [])), 0)
        total_pages = max(1, (total + limit - 1) // limit) if total > 0 else 1
        meta = {"page": page, "limit": limit, "total": total, "totalPages": total_pages}
        return [_serialize(s) for s in items], meta

    async def find_by_id_populated(self, sale_id: str) -> dict:
        try:
            pipeline = [
                {"$match": {"_id": ObjectId(sale_id)}},
                {
                    "$lookup": {
                        "from": "users",
                        "localField": "soldBy",
                        "foreignField": "_id",
                        "pipeline": [{"$project": {"name": 1, "email": 1}}],
                        "as": "soldBy",
                    }
                },
                {"$unwind": {"path": "$soldBy", "preserveNullAndEmptyArrays": True}},
                {
                    "$lookup": {
                        "from": "products",
                        "localField": "items.product",
                        "foreignField": "_id",
                        "pipeline": [
                            {
                                "$project": {
                                    "name": 1,
                                    "sku": 1,
                                    "sellingPrice": 1,
                                    "imageUrl": 1,
                                    "stockQuantity": 1,
                                    "category": 1,
                                }
                            }
                        ],
                        "as": "_productDetails",
                    }
                },
            ]
            cursor = await self.db["sales"].aggregate(pipeline)
            sales = await cursor.to_list(length=1)
            if not sales:
                raise AppException("Sale not found", HttpStatus.NOT_FOUND)
            sale = sales[0]
            product_map = {str(p["_id"]): p for p in sale.pop("_productDetails", [])}
            for item in sale.get("items", []):
                pid = (
                    str(item["product"])
                    if isinstance(item["product"], ObjectId)
                    else item["product"]
                )
                item["product"] = product_map.get(pid, item["product"])
            return _serialize(sale)
        except AppException:
            raise
        except Exception:
            raise AppException("Sale not found", HttpStatus.NOT_FOUND)
