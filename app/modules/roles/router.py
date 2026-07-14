from fastapi import APIRouter, Depends

from app.core.deps import require_role
from app.core.http_status import HttpStatus
from app.infrastructure.mongo.client import get_db
from app.modules.roles import service as roles_service
from app.modules.roles.schemas import (
    CreatePermissionRequest,
    CreateRoleRequest,
    UpdatePermissionRequest,
    UpdateRoleRequest,
)
from app.schemas.response import ApiResponse

admin_only = require_role("admin")

roles_router = APIRouter(prefix="/roles")


@roles_router.get("")
async def list_roles(db=Depends(get_db), _user: dict = Depends(admin_only)):
    roles = await roles_service.get_roles(db)
    return ApiResponse.success("Roles fetched successfully", roles)


@roles_router.get("/{role_id}")
async def get_role(role_id: str, db=Depends(get_db), _user: dict = Depends(admin_only)):
    role = await roles_service.get_role(db, role_id)
    return ApiResponse.success("Role fetched successfully", role)


@roles_router.post("")
async def create_role(
    data: CreateRoleRequest, db=Depends(get_db), _user: dict = Depends(admin_only)
):
    role = await roles_service.create_role(db, data.model_dump())
    return ApiResponse.success(
        "Role created successfully", role, status_code=HttpStatus.CREATED
    )


@roles_router.put("/{role_id}")
async def update_role(
    role_id: str,
    data: UpdateRoleRequest,
    db=Depends(get_db),
    _user: dict = Depends(admin_only),
):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    role = await roles_service.update_role(db, role_id, updates)
    return ApiResponse.success("Role updated successfully", role)


@roles_router.delete("/{role_id}")
async def delete_role(
    role_id: str, db=Depends(get_db), _user: dict = Depends(admin_only)
):
    role = await roles_service.delete_role(db, role_id)
    return ApiResponse.success("Role deleted successfully", role)


permissions_router = APIRouter(prefix="/permissions")


@permissions_router.get("")
async def list_permissions(db=Depends(get_db), _user: dict = Depends(admin_only)):
    perms = await roles_service.get_permissions(db)
    return ApiResponse.success("Permissions fetched successfully", perms)


@permissions_router.get("/{perm_id}")
async def get_permission(
    perm_id: str, db=Depends(get_db), _user: dict = Depends(admin_only)
):
    perm = await roles_service.get_permission(db, perm_id)
    return ApiResponse.success("Permission fetched successfully", perm)


@permissions_router.post("")
async def create_permission(
    data: CreatePermissionRequest, db=Depends(get_db), _user: dict = Depends(admin_only)
):
    perm = await roles_service.create_permission(db, data.model_dump())
    return ApiResponse.success(
        "Permission created successfully", perm, status_code=HttpStatus.CREATED
    )


@permissions_router.put("/{perm_id}")
async def update_permission(
    perm_id: str,
    data: UpdatePermissionRequest,
    db=Depends(get_db),
    _user: dict = Depends(admin_only),
):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    perm = await roles_service.update_permission(db, perm_id, updates)
    return ApiResponse.success("Permission updated successfully", perm)


@permissions_router.delete("/{perm_id}")
async def delete_permission(
    perm_id: str, db=Depends(get_db), _user: dict = Depends(admin_only)
):
    perm = await roles_service.delete_permission(db, perm_id)
    return ApiResponse.success("Permission deleted successfully", perm)
