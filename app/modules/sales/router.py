from fastapi import APIRouter, Depends, Query, Request

from app.core.deps import get_current_user, require_role
from app.core.http_status import HttpStatus
from app.infrastructure.mongo.client import get_db
from app.infrastructure.rate_limiter import rate_limit
from app.modules.sales import service as sale_service
from app.modules.sales.schemas import CreateSaleRequest
from app.schemas.response import ApiResponse

create_role = require_role("admin", "manager", "employee")

router = APIRouter(prefix="/sales")


@router.post("")
@rate_limit(60, 60)
async def create_sale(
    request: Request,
    data: CreateSaleRequest,
    db=Depends(get_db),
    user: dict = Depends(create_role),
):
    result = await sale_service.create_sale(db, data.model_dump(), user["id"])
    return ApiResponse.success(
        "Sale created successfully", result, status_code=HttpStatus.CREATED
    )


@router.get("")
async def list_sales(
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    sort: str = Query(default="-createdAt"),
    db=Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    items, meta = await sale_service.get_sales(
        db, search=search, page=page, limit=limit, sort=sort
    )
    return ApiResponse.success("Sales fetched successfully", items, meta)


@router.get("/{sale_id}")
async def get_sale(
    sale_id: str, db=Depends(get_db), _user: dict = Depends(get_current_user)
):
    doc = await sale_service.get_sale_by_id(db, sale_id)
    return ApiResponse.success("Sale fetched successfully", doc)
