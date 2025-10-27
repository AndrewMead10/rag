from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..database.models import User
from ..database.shared import get_dashboard_metrics
from ..middleware.auth import get_current_user

router = APIRouter()


class DashboardUserStats(BaseModel):
    user_id: int
    email: str
    account_created: str


class DashboardSystemMetrics(BaseModel):
    total_users: int
    active_users: int
    pending_resets: int


class DashboardData(BaseModel):
    user_stats: DashboardUserStats
    system_metrics: DashboardSystemMetrics


@router.get("/dashboard/onload", response_model=DashboardData)
async def dashboard_onload(current_user: User = Depends(get_current_user)):
    """
    Gather all data needed for dashboard display.
    Single endpoint to minimize frontend API calls.
    """
    system_metrics = get_dashboard_metrics()
    user_stats = DashboardUserStats(
        user_id=current_user.id,
        email=current_user.email,
        account_created=current_user.created_at.isoformat(),
    )
    
    return DashboardData(user_stats=user_stats, system_metrics=DashboardSystemMetrics(**system_metrics))


@router.post("/dashboard/onsubmit")
async def dashboard_onsubmit(
    action_data: dict,
    current_user: User = Depends(get_current_user),
):
    """Handle dashboard actions (e.g., updating preferences)"""
    return {"success": True, "message": "Dashboard action completed"}
