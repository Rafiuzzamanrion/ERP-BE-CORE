from app.core.exceptions import AppException
from app.core.http_status import HttpStatus
from app.infrastructure.cloudinary import delete_image, upload_image
from app.infrastructure.logging import create_logger
from app.modules.categories.repository import CategoryRepository
from app.modules.products.repository import ProductRepository

logger = create_logger(__name__)


async def create_product(
    db, data: dict, file_bytes: bytes | None, user_id: str
) -> dict:
    repo = ProductRepository(db)
    cat_repo = CategoryRepository(db)
    sku = data["sku"].strip().upper()
    existing = await repo.find_by_sku(sku)
    if existing:
        raise AppException("SKU already exists", HttpStatus.CONFLICT)
    if not file_bytes:
        raise AppException("Product image is required", HttpStatus.BAD_REQUEST)
    category_name = data["category"].strip().lower()
    if not await cat_repo.exists(category_name):
        raise AppException("Category does not exist", HttpStatus.BAD_REQUEST)
    uploaded = await upload_image(file_bytes, "erp/products")
    doc = {
        "name": data["name"].strip(),
        "sku": sku,
        "category": category_name,
        "purchasePrice": data["purchasePrice"],
        "sellingPrice": data["sellingPrice"],
        "stockQuantity": data.get("stockQuantity", 0),
        "imageUrl": uploaded["secure_url"],
        "imagePublicId": uploaded["public_id"],
        "createdBy": user_id,
    }
    return await repo.create(doc)


async def get_products(
    db,
    search: str | None = None,
    category: str | None = None,
    page: int = 1,
    limit: int = 10,
    sort: str = "-createdAt",
) -> tuple[list[dict], dict]:
    return await ProductRepository(db).list_paginated(
        search=search, category=category, page=page, limit=limit, sort=sort
    )


async def get_product_by_id(db, product_id: str) -> dict:
    product = await ProductRepository(db).find_by_id(product_id)
    if not product:
        raise AppException("Product not found", HttpStatus.NOT_FOUND)
    return product


async def update_product(
    db, product_id: str, data: dict, file_bytes: bytes | None = None
) -> dict:
    repo = ProductRepository(db)
    cat_repo = CategoryRepository(db)
    product = await repo.find_by_id(product_id)
    if not product:
        raise AppException("Product not found", HttpStatus.NOT_FOUND)

    updates = {}
    if data.get("sku"):
        sku = data["sku"].strip().upper()
        if sku != product.get("sku"):
            existing = await repo.find_by_sku(sku)
            if existing:
                raise AppException("SKU already exists", HttpStatus.CONFLICT)
        updates["sku"] = sku
    else:
        updates["sku"] = product.get("sku")
    if file_bytes:
        if product.get("imagePublicId"):
            await delete_image(product["imagePublicId"])
        uploaded = await upload_image(file_bytes, "erp/products")
        updates["imageUrl"] = uploaded["secure_url"]
        updates["imagePublicId"] = uploaded["public_id"]
    if data.get("category") is not None:
        category_name = data["category"].strip().lower()
        if not await cat_repo.exists(category_name):
            raise AppException("Category does not exist", HttpStatus.BAD_REQUEST)
        updates["category"] = category_name
    if data.get("name") is not None:
        updates["name"] = data["name"].strip()
    if data.get("purchasePrice") is not None:
        updates["purchasePrice"] = data["purchasePrice"]
    if data.get("sellingPrice") is not None:
        updates["sellingPrice"] = data["sellingPrice"]
    if data.get("stockQuantity") is not None:
        updates["stockQuantity"] = data["stockQuantity"]

    if updates:
        return await repo.update(product_id, updates)
    return product


async def delete_product(db, product_id: str) -> dict:
    repo = ProductRepository(db)
    product = await repo.find_by_id(product_id)
    if not product:
        raise AppException("Product not found", HttpStatus.NOT_FOUND)
    if product.get("imagePublicId"):
        await delete_image(product["imagePublicId"])
    await repo.delete(product_id)
    return product
