from fastapi import APIRouter, Depends, Request

from app.core.deps import get_current_user
from app.infrastructure.mongo.client import get_db
from app.infrastructure.rate_limiter import rate_limit
from app.modules.auth import service as auth_service
from app.modules.auth.schemas import LoginRequest
from app.schemas.response import ApiResponse

router = APIRouter(prefix="/auth")


@router.post("/login")
@rate_limit(20, 900)
async def login(request: Request, data: LoginRequest, db=Depends(get_db)):
    result = await auth_service.login(db, data.email, data.password)
    return ApiResponse.success("Login successful", result)


@router.get("/me")
async def me(user: dict = Depends(get_current_user), db=Depends(get_db)):
    result = await auth_service.get_me(db, user["id"])
    return ApiResponse.success("User retrieved successfully", result)


@router.post("/logout")
async def logout(_user: dict = Depends(get_current_user)):
    return ApiResponse.success("Logged out successfully")
