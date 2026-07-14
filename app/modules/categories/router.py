from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user, require_role
from app.core.http_status import HttpStatus
from app.infrastructure.mongo.client import get_db
from app.modules.categories import service as category_service
from app.modules.categories.schemas import CreateCategoryRequest, UpdateCategoryRequest
from app.schemas.response import ApiResponse

router = APIRouter(prefix="/categories")

admin_or_manager = require_role("admin", "manager")


@router.get("")
async def list_categories(
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    sort: str = Query(default="name"),
    db=Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    items, meta = await category_service.get_categories(
        db, search=search, page=page, limit=limit, sort=sort
    )
    return ApiResponse.success("Categories fetched successfully", items, meta)


@router.get("/{category_id}")
async def get_category(
    category_id: str, db=Depends(get_db), _user: dict = Depends(get_current_user)
):
    doc = await category_service.get_category(db, category_id)
    return ApiResponse.success("Category fetched successfully", doc)


@router.post("")
async def create_category(
    data: CreateCategoryRequest,
    db=Depends(get_db),
    _user: dict = Depends(admin_or_manager),
):
    result = await category_service.create_category(db, data.model_dump())
    return ApiResponse.success(
        "Category created successfully", result, status_code=HttpStatus.CREATED
    )


@router.put("/{category_id}")
async def update_category(
    category_id: str,
    data: UpdateCategoryRequest,
    db=Depends(get_db),
    _user: dict = Depends(admin_or_manager),
):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    result = await category_service.update_category(db, category_id, updates)
    return ApiResponse.success("Category updated successfully", result)


@router.delete("/{category_id}")
async def delete_category(
    category_id: str, db=Depends(get_db), _user: dict = Depends(require_role("admin"))
):
    await category_service.delete_category(db, category_id)
    return ApiResponse.success("Category deleted successfully")
