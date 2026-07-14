from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user
from app.infrastructure.mongo.client import get_db
from app.modules.dashboard import service as dashboard_service
from app.schemas.response import ApiResponse

router = APIRouter(prefix="/dashboard")


@router.get("/stats")
async def get_stats(
    startDate: str | None = Query(default=None),
    endDate: str | None = Query(default=None),
    db=Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    data = await dashboard_service.get_stats(db, start_date=startDate, end_date=endDate)
    return ApiResponse.success("Dashboard stats retrieved successfully", data)


@router.get("/low-stock-alerts")
async def get_low_stock_alerts(
    db=Depends(get_db), _user: dict = Depends(get_current_user)
):
    data = await dashboard_service.get_low_stock_alerts(db)
    return ApiResponse.success("Low stock alerts retrieved successfully", data)
