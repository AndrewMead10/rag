from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from .me import UserResponse as AuthUser
from ...middleware.auth import (
    verify_password,
    get_user_roles_with_hierarchy,
    set_auth_cookies,
)
from ...database.shared import get_user_by_email

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    user: AuthUser


@router.post("/auth/login/onsubmit", response_model=LoginResponse)
async def login_onsubmit(credentials: LoginRequest, response: Response):
    """Handle user login"""
    user = get_user_by_email(credentials.email)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account is disabled")
    
    set_auth_cookies(response, user.id)
    
    roles = list(get_user_roles_with_hierarchy(user.id))

    return LoginResponse(
        success=True,
        user=AuthUser(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            roles=roles,
            created_at=user.created_at.isoformat() if getattr(user, "created_at", None) else None,
        ),
    )
