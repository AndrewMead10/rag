from fastapi import APIRouter, Depends, Request, Response, HTTPException
from jose import jwt, JWTError
from pydantic import BaseModel

from ...middleware.auth import get_current_user, get_user_roles_with_hierarchy, create_access_token, verify_token
from ...database.models import User
from ...config import settings

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


@router.post("/auth/refresh")
async def refresh_token(request: Request, response: Response):
    """Refresh access token using refresh token from cookie"""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token or not verify_token(refresh_token):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    try:
        payload = jwt.decode(refresh_token, settings.jwt_secret, algorithms=["HS256"])
        user_id = int(payload["sub"])
        token_type = payload.get("type")

        if token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access_token = create_access_token(user_id)
    response.set_cookie(
        "access_token",
        new_access_token,
        httponly=True,
        max_age=settings.access_token_ttl_minutes * 60,
        samesite="lax"
    )

    return {"success": True}