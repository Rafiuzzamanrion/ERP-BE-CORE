from fastapi import APIRouter, Depends, Query, Request

from app.core.deps import require_role
from app.core.http_status import HttpStatus
from app.infrastructure.mongo.client import get_db
from app.infrastructure.rate_limiter import rate_limit
from app.modules.users import service as user_service
from app.modules.users.schemas import CreateUserRequest, UpdateUserRequest
from app.schemas.response import ApiResponse

router = APIRouter(prefix="/users")

admin_only = require_role("admin")


@router.get("")
async def get_users(
    search: str | None = Query(default=None),
    db=Depends(get_db),
    user: dict = Depends(admin_only),
):
    users = await user_service.list_users(db, search)
    return ApiResponse.success("Users retrieved successfully", users)


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    db=Depends(get_db),
    _user: dict = Depends(admin_only),
):
    doc = await user_service.find_by_id(db, user_id)
    return ApiResponse.success("User retrieved successfully", doc)


@router.post("")
@rate_limit(10, 3600)
async def create_user(
    request: Request,
    data: CreateUserRequest,
    db=Depends(get_db),
    _user: dict = Depends(admin_only),
):
    result = await user_service.create_user(db, data.model_dump())
    return ApiResponse.success(
        "User created successfully", result, status_code=HttpStatus.CREATED
    )


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    data: UpdateUserRequest,
    db=Depends(get_db),
    _user: dict = Depends(admin_only),
):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    result = await user_service.update_user(db, user_id, updates)
    return ApiResponse.success("User updated successfully", result)


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db=Depends(get_db),
    _user: dict = Depends(admin_only),
):
    await user_service.delete_user(db, user_id)
    return ApiResponse.success("User deleted successfully")
