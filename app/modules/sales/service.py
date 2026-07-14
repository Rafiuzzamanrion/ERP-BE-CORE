from app.infrastructure.logging import create_logger
from app.modules.sales.repository import SaleRepository
from app.socketio import sio

logger = create_logger(__name__)


async def create_sale(db, data: dict, user_id: str) -> dict:
    repo = SaleRepository(db, sio=sio)
    return await repo.create_transaction(data, user_id)


async def get_sales(
    db,
    search: str | None = None,
    page: int = 1,
    limit: int = 10,
    sort: str = "-createdAt",
) -> tuple[list[dict], dict]:
    return await SaleRepository(db).list_paginated(
        search=search, page=page, limit=limit, sort=sort
    )


async def get_sale_by_id(db, sale_id: str) -> dict:
    return await SaleRepository(db).find_by_id_populated(sale_id)
