from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ...middleware.auth import get_current_user, get_user_roles_with_hierarchy
from ...database.models import User

router = APIRouter()


class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    roles: list[str]
    created_at: str | None = None


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    roles = list(get_user_roles_with_hierarchy(current_user.id))
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        is_active=current_user.is_active,
        roles=roles,
        created_at=current_user.created_at.isoformat() if getattr(current_user, "created_at", None) else None,
    )
