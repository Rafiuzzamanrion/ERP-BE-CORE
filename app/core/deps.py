import jwt
from bson import ObjectId
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import verify_token
from app.infrastructure.cache import permission_cache
from app.infrastructure.logging import create_logger
from app.infrastructure.mongo.client import get_db

logger = create_logger(__name__)

security = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials
    try:
        payload = verify_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    user_id = payload.get("id")
    user_role = payload.get("role", "")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )

    request.state.user_id = user_id
    request.state.user_role = user_role
    return {"id": user_id, "role": user_role}


class RoleChecker:
    def __init__(self, *allowed_roles: str):
        self.allowed_roles = allowed_roles

    async def __call__(
        self, request: Request, user: dict = Depends(get_current_user)
    ) -> dict:
        if not self.allowed_roles:
            return user

        role_name = await _resolve_role_name(user.get("role", ""))
        if not role_name or role_name not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return user


class PermissionChecker:
    def __init__(self, permission_key: str):
        self.permission_key = permission_key

    async def __call__(self, user: dict = Depends(get_current_user)) -> dict:
        role_id = user.get("role", "")
        if not role_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )

        hit, cached_data = await permission_cache.get(role_id)
        if hit:
            if self.permission_key in cached_data.get("permissions", []):
                return user
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )

        role_data = await _fetch_and_cache_role(role_id)
        if not role_data:
            await permission_cache.set(
                role_id, {"roleName": "unknown", "permissions": []}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )

        if self.permission_key in role_data.get("permissions", []):
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )


async def _resolve_role_name(role_id: str) -> str | None:
    if not role_id:
        return None

    hit, cached_data = await permission_cache.get(role_id)
    if hit:
        return cached_data.get("roleName")

    role_data = await _fetch_and_cache_role(role_id)
    return role_data.get("roleName") if role_data else None


async def _fetch_and_cache_role(role_id: str) -> dict | None:
    try:
        db = get_db()
        pipeline = [
            {"$match": {"_id": ObjectId(role_id)}},
            {
                "$lookup": {
                    "from": "permissions",
                    "localField": "permissions",
                    "foreignField": "_id",
                    "as": "permissions",
                }
            },
        ]
        cursor = await db["roles"].aggregate(pipeline)
        roles = await cursor.to_list(length=1)
        if not roles:
            return None

        role = roles[0]
        permission_keys = [p["key"] for p in role.get("permissions", [])]
        data = {"permissions": permission_keys, "roleName": role["name"]}
        await permission_cache.set(role_id, data)
        return data
    except Exception as e:
        logger.error("fetch_role_failed", role_id=role_id, error=str(e))
        return None


async def clear_permission_cache(role_id: str):
    await permission_cache.invalidate(role_id)


require_role = RoleChecker
require_permission = PermissionChecker
