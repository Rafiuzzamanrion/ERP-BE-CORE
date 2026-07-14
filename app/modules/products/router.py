from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile

from app.core.deps import get_current_user, require_role
from app.core.http_status import HttpStatus
from app.infrastructure.mongo.client import get_db
from app.infrastructure.rate_limiter import rate_limit
from app.modules.products import service as product_service
from app.schemas.response import ApiResponse

router = APIRouter(prefix="/products")

admin_or_manager = require_role("admin", "manager")


@router.get("")
async def list_products(
    search: str | None = Query(default=None),
    category: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    sort: str = Query(default="-createdAt"),
    db=Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    items, meta = await product_service.get_products(
        db, search=search, category=category, page=page, limit=limit, sort=sort
    )
    return ApiResponse.success("Products fetched successfully", items, meta)


@router.get("/{product_id}")
async def get_product(
    product_id: str, db=Depends(get_db), _user: dict = Depends(get_current_user)
):
    doc = await product_service.get_product_by_id(db, product_id)
    return ApiResponse.success("Product fetched successfully", doc)


@router.post("")
@rate_limit(30, 60)
async def create_product(
    request: Request,
    name: str = Form(min_length=1, max_length=100),
    sku: str = Form(min_length=1, max_length=50),
    category: str = Form(min_length=1, max_length=50),
    purchasePrice: str = Form(),
    sellingPrice: str = Form(),
    stockQuantity: str = Form("0"),
    image: UploadFile = File(...),
    db=Depends(get_db),
    user: dict = Depends(admin_or_manager),
):
    data = {
        "name": name,
        "sku": sku,
        "category": category,
        "purchasePrice": float(purchasePrice),
        "sellingPrice": float(sellingPrice),
        "stockQuantity": int(stockQuantity),
    }
    file_bytes = await image.read()
    result = await product_service.create_product(db, data, file_bytes, user["id"])
    return ApiResponse.success(
        "Product created successfully", result, status_code=HttpStatus.CREATED
    )


@router.put("/{product_id}")
async def update_product(
    product_id: str,
    name: str | None = Form(None),
    sku: str | None = Form(None),
    category: str | None = Form(None),
    purchasePrice: str | None = Form(None),
    sellingPrice: str | None = Form(None),
    stockQuantity: str | None = Form(None),
    image: UploadFile | None = File(None),
    db=Depends(get_db),
    _user: dict = Depends(admin_or_manager),
):
    data = {}
    if name is not None:
        data["name"] = name
    if sku is not None:
        data["sku"] = sku
    if category is not None:
        data["category"] = category
    if purchasePrice is not None:
        data["purchasePrice"] = float(purchasePrice)
    if sellingPrice is not None:
        data["sellingPrice"] = float(sellingPrice)
    if stockQuantity is not None:
        data["stockQuantity"] = int(stockQuantity)
    file_bytes = await image.read() if image else None
    result = await product_service.update_product(db, product_id, data, file_bytes)
    return ApiResponse.success("Product updated successfully", result)


@router.delete("/{product_id}")
async def delete_product(
    product_id: str, db=Depends(get_db), _user: dict = Depends(admin_or_manager)
):
    await product_service.delete_product(db, product_id)
    return ApiResponse.success("Product deleted successfully")
