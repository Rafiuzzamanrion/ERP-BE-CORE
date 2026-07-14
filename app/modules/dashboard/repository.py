from datetime import datetime

from app.infrastructure.logging import create_logger

logger = create_logger(__name__)


class DashboardRepository:
    def __init__(self, db):
        self.db = db

    async def count_products(self) -> int:
        return await self.db["products"].count_documents({})

    async def get_low_stock_products(self) -> list[dict]:
        cursor = await self.db["products"].aggregate(
            [
                {"$match": {"stockQuantity": {"$lt": 5}}},
                {
                    "$project": {
                        "name": 1,
                        "sku": 1,
                        "stockQuantity": 1,
                        "_id": {"$toString": "$_id"},
                    }
                },
            ]
        )
        return await cursor.to_list(length=None)

    async def get_sales_revenue(self, date_match: dict) -> tuple[float, int]:
        cursor = await self.db["sales"].aggregate(
            [
                {"$match": date_match},
                {
                    "$group": {
                        "_id": None,
                        "totalRevenue": {"$sum": "$grandTotal"},
                        "totalSales": {"$sum": 1},
                    }
                },
            ]
        )
        results = await cursor.to_list(length=1)
        rev = results[0] if results else {}
        return rev.get("totalRevenue", 0), rev.get("totalSales", 0)

    async def count_sales(self, date_match: dict) -> int:
        return await self.db["sales"].count_documents(date_match)

    async def get_daily_revenue(self, seven_days_ago: datetime) -> list[dict]:
        cursor = await self.db["sales"].aggregate(
            [
                {"$match": {"createdAt": {"$gte": seven_days_ago}}},
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$createdAt",
                            }
                        },
                        "revenue": {"$sum": "$grandTotal"},
                        "sales": {"$sum": 1},
                    }
                },
                {"$sort": {"_id": 1}},
            ]
        )
        return await cursor.to_list(length=None)

    async def get_category_revenue(self) -> list[dict]:
        cursor = await self.db["sales"].aggregate(
            [
                {"$unwind": "$items"},
                {
                    "$lookup": {
                        "from": "products",
                        "localField": "items.product",
                        "foreignField": "_id",
                        "as": "_product",
                    }
                },
                {"$unwind": {"path": "$_product", "preserveNullAndEmptyArrays": True}},
                {
                    "$group": {
                        "_id": "$_product.category",
                        "revenue": {"$sum": "$items.subtotal"},
                    }
                },
                {"$sort": {"revenue": -1}},
                {"$limit": 8},
            ]
        )
        return await cursor.to_list(length=None)

    async def get_recent_sales(self) -> list[dict]:
        cursor = await self.db["sales"].aggregate(
            [
                {"$sort": {"createdAt": -1}},
                {"$limit": 5},
                {
                    "$lookup": {
                        "from": "users",
                        "localField": "soldBy",
                        "foreignField": "_id",
                        "pipeline": [{"$project": {"name": 1}}],
                        "as": "soldBy",
                    }
                },
                {"$unwind": {"path": "$soldBy", "preserveNullAndEmptyArrays": True}},
                {
                    "$project": {
                        "_id": {"$toString": "$_id"},
                        "grandTotal": 1,
                        "createdAt": 1,
                        "soldBy._id": {"$toString": "$soldBy._id"},
                        "soldBy.name": 1,
                        "items": 1,
                    }
                },
            ]
        )
        return await cursor.to_list(length=None)
