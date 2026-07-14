import asyncio
from datetime import UTC, datetime, timedelta

from app.infrastructure.cache import dashboard_cache
from app.infrastructure.logging import create_logger
from app.modules.dashboard.repository import DashboardRepository

logger = create_logger(__name__)


async def get_stats(
    db, start_date: str | None = None, end_date: str | None = None
) -> dict:
    cache_key = (
        f"stats-{start_date or ''}-{end_date or ''}"
        if (start_date or end_date)
        else "stats-default"
    )

    hit, cached = await dashboard_cache.get(cache_key)
    if hit:
        return cached

    repo = DashboardRepository(db)

    total_products_f = repo.count_products()
    low_stock_f = repo.get_low_stock_products()

    total_products, low_stock_products = await asyncio.gather(
        total_products_f, low_stock_f
    )

    date_match: dict = {}
    if start_date:
        date_match.setdefault("createdAt", {})["$gte"] = datetime.fromisoformat(
            start_date
        )
    if end_date:
        date_match.setdefault("createdAt", {})["$lte"] = datetime.fromisoformat(
            end_date
        )

    total_sales_f = repo.count_sales(date_match)
    rev_f = repo.get_sales_revenue(date_match)
    daily_f = repo.get_daily_revenue(
        datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        - timedelta(days=6)
    )
    cat_f = repo.get_category_revenue()
    recent_f = repo.get_recent_sales()

    (
        total_sales_docs,
        rev_tup,
        daily_revenue,
        category_revenue,
        recent_sales_agg,
    ) = await asyncio.gather(total_sales_f, rev_f, daily_f, cat_f, recent_f)

    total_revenue, total_sales_agg = rev_tup
    total_sales = total_sales_docs

    daily = [
        {"date": d["_id"], "revenue": d["revenue"], "sales": d["sales"]}
        for d in daily_revenue
    ]
    cat_rev = [
        {"category": c["_id"] or "Uncategorized", "revenue": c["revenue"]}
        for c in category_revenue
    ]
    recent_sales = [
        {
            "_id": s["_id"],
            "grandTotal": s["grandTotal"],
            "createdAt": s["createdAt"].isoformat()
            if isinstance(s.get("createdAt"), datetime)
            else s.get("createdAt"),
            "soldBy": s["soldBy"],
            "items": [
                {
                    "productName": i.get("productName"),
                    "quantity": i.get("quantity"),
                    "subtotal": i.get("subtotal"),
                }
                for i in (s.get("items") or [])
            ],
        }
        for s in recent_sales_agg
    ]

    result = {
        "totalProducts": total_products,
        "totalSales": total_sales,
        "lowStockProducts": low_stock_products,
        "lowStockCount": len(low_stock_products),
        "totalRevenue": total_revenue,
        "recentSales": recent_sales,
        "dailyRevenue": daily,
        "categoryRevenue": cat_rev,
    }

    await dashboard_cache.set(cache_key, result)
    return result


async def get_low_stock_alerts(db) -> dict:
    repo = DashboardRepository(db)
    products = await repo.get_low_stock_products()
    return {"lowStockCount": len(products), "lowStockProducts": products}
