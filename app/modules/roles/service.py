from bson import ObjectId

from app.core.exceptions import AppException
from app.core.http_status import HttpStatus
from app.infrastructure.logging import create_logger
from app.modules.roles.repository import PermissionRepository, RoleRepository

logger = create_logger(__name__)


def _to_oid_list(ids: list[str]) -> list[ObjectId]:
    return [ObjectId(i) for i in ids]


# ── Role ───────────────────────────────────────────────────────────


async def create_role(db, data: dict) -> dict:
    repo = RoleRepository(db)
    existing = await repo.find_by_name(data["name"])
    if existing:
        raise AppException("Role with this name already exists", HttpStatus.CONFLICT)
    doc = {
        "name": data["name"],
        "permissions": _to_oid_list(data.get("permissions") or []),
        "isSystem": data.get("isSystem", False),
    }
    return await repo.create(doc)


async def get_roles(db) -> list[dict]:
    return await RoleRepository(db).list_all()


async def get_role(db, role_id: str) -> dict:
    role = await RoleRepository(db).find_by_id(role_id)
    if not role:
        raise AppException("Role not found", HttpStatus.NOT_FOUND)
    return role


async def update_role(db, role_id: str, data: dict) -> dict:
    repo = RoleRepository(db)
    role = await repo.find_by_id(role_id)
    if not role:
        raise AppException("Role not found", HttpStatus.NOT_FOUND)

    updates = {}
    if data.get("name") and data["name"] != role.get("name"):
        existing = await repo.find_by_name(data["name"])
        if existing:
            raise AppException(
                "Role with this name already exists", HttpStatus.CONFLICT
            )
        updates["name"] = data["name"]

    if data.get("permissions") is not None:
        updates["permissions"] = _to_oid_list(data["permissions"])
    if data.get("isSystem") is not None:
        updates["isSystem"] = data["isSystem"]

    if updates:
        return await repo.update(role_id, updates)
    return role


async def delete_role(db, role_id: str) -> dict:
    repo = RoleRepository(db)
    role = await repo.find_by_id(role_id)
    if not role:
        raise AppException("Role not found", HttpStatus.NOT_FOUND)
    if role.get("isSystem"):
        raise AppException("Cannot delete a system role", HttpStatus.FORBIDDEN)
    return await repo.delete(role_id)


# ── Permission ──────────────────────────────────────────────────────


async def create_permission(db, data: dict) -> dict:
    repo = PermissionRepository(db)
    existing = await repo.find_by_key(data["key"])
    if existing:
        raise AppException(
            "Permission with this key already exists", HttpStatus.CONFLICT
        )
    return await repo.create(data)


async def get_permissions(db) -> list[dict]:
    return await PermissionRepository(db).list_all()


async def get_permission(db, perm_id: str) -> dict:
    perm = await PermissionRepository(db).find_by_id(perm_id)
    if not perm:
        raise AppException("Permission not found", HttpStatus.NOT_FOUND)
    return perm


async def update_permission(db, perm_id: str, data: dict) -> dict:
    repo = PermissionRepository(db)
    perm = await repo.find_by_id(perm_id)
    if not perm:
        raise AppException("Permission not found", HttpStatus.NOT_FOUND)

    updates = {}
    if data.get("key") and data["key"] != perm.get("key"):
        existing = await repo.find_by_key(data["key"])
        if existing:
            raise AppException(
                "Permission with this key already exists", HttpStatus.CONFLICT
            )
        updates["key"] = data["key"].strip()
    if data.get("description") is not None:
        updates["description"] = data["description"].strip()

    if updates:
        return await repo.update(perm_id, updates)
    return perm


async def delete_permission(db, perm_id: str) -> dict:
    repo = PermissionRepository(db)
    perm = await repo.find_by_id(perm_id)
    if not perm:
        raise AppException("Permission not found", HttpStatus.NOT_FOUND)
    return await repo.delete(perm_id)
