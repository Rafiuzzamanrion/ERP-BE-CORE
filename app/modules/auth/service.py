from app.core.exceptions import AppException
from app.core.http_status import HttpStatus
from app.core.security import create_access_token, verify_password
from app.modules.auth.repository import AuthRepository


async def login(db, email: str, password: str) -> dict:
    repo = AuthRepository(db)
    user = await repo.find_user_by_email(email)
    if not user:
        raise AppException("Invalid email or password", HttpStatus.UNAUTHORIZED)

    stored_password = user.get("password", "")
    if not verify_password(password, stored_password):
        raise AppException("Invalid email or password", HttpStatus.UNAUTHORIZED)

    if not user.get("isActive", True):
        raise AppException(
            "Your account has been deactivated. Please contact an administrator.",
            HttpStatus.UNAUTHORIZED,
        )

    role_id = str(user.get("role", "")) or "employee"
    role_name = await repo.resolve_role_name(user.get("role"))

    token = create_access_token({"id": str(user["_id"]), "role": role_id})

    return {
        "token": token,
        "user": {
            "_id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "role": role_name,
            "isActive": user.get("isActive", True),
        },
    }


async def get_me(db, user_id: str) -> dict:
    repo = AuthRepository(db)
    user = await repo.find_user_by_id(user_id)
    if not user:
        raise AppException("User not found", HttpStatus.NOT_FOUND)

    role_name = await repo.resolve_role_name(user.get("role"))

    return {
        "_id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "role": role_name,
        "isActive": user.get("isActive", True),
    }
