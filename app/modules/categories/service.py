from app.core.exceptions import AppException
from app.core.http_status import HttpStatus
from app.infrastructure.logging import create_logger
from app.modules.categories.repository import CategoryRepository

logger = create_logger(__name__)


async def create_category(db, data: dict) -> dict:
    repo = CategoryRepository(db)
    name = data["name"].strip().lower()
    existing = await repo.find_by_name(name)
    if existing:
        raise AppException(
            "Category with this name already exists", HttpStatus.CONFLICT
        )
    doc = {"name": name, "description": (data.get("description") or "").strip()}
    return await repo.create(doc)


async def get_categories(
    db, search: str | None = None, page: int = 1, limit: int = 10, sort: str = "name"
) -> tuple[list[dict], dict]:
    return await CategoryRepository(db).list_paginated(
        search=search, page=page, limit=limit, sort=sort
    )


async def get_category(db, category_id: str) -> dict:
    category = await CategoryRepository(db).find_by_id(category_id)
    if not category:
        raise AppException("Category not found", HttpStatus.NOT_FOUND)
    return category


async def update_category(db, category_id: str, data: dict) -> dict:
    repo = CategoryRepository(db)
    category = await repo.find_by_id(category_id)
    if not category:
        raise AppException("Category not found", HttpStatus.NOT_FOUND)
    updates = {}
    if data.get("name") and data["name"].strip().lower() != category["name"]:
        name = data["name"].strip().lower()
        existing = await repo.find_by_name(name)
        if existing:
            raise AppException(
                "Category with this name already exists", HttpStatus.CONFLICT
            )
        updates["name"] = name
    if data.get("description") is not None:
        updates["description"] = data["description"].strip()
    if updates:
        return await repo.update(category_id, updates)
    return category


async def delete_category(db, category_id: str):
    repo = CategoryRepository(db)
    category = await repo.find_by_id(category_id)
    if not category:
        raise AppException("Category not found", HttpStatus.NOT_FOUND)
    products_count = await repo.count_products_using(category["name"])
    if products_count > 0:
        raise AppException(
            "Cannot delete category: it is still used by products", HttpStatus.CONFLICT
        )
    await repo.delete(category_id)


async def category_exists(db, name: str) -> bool:
    return await CategoryRepository(db).exists(name)
