from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, EmailStr
from .me import UserResponse as AuthUser
from ...middleware.auth import (
    get_password_hash,
    create_access_token,
    create_refresh_token,
    get_user_roles_with_hierarchy,
)
from ...database.shared import get_user_by_email, create_user
from ...config import settings

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    success: bool
    message: str
    user: AuthUser


@router.post("/auth/register/onsubmit", response_model=RegisterResponse)
async def register_onsubmit(user_data: RegisterRequest, response: Response):
    """Handle user registration"""
    if not settings.enable_user_registration:
        raise HTTPException(status_code=403, detail="Registration is disabled")
    
    existing_user = get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if len(user_data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    hashed_password = get_password_hash(user_data.password)
    user = create_user(user_data.email, hashed_password)

    # Generate tokens and set cookies for automatic login
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        max_age=settings.access_token_ttl_minutes * 60,
        samesite="lax",
        secure=getattr(settings, "cookie_secure", False),
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        max_age=settings.refresh_token_ttl_days * 24 * 60 * 60,
        samesite="lax",
        secure=getattr(settings, "cookie_secure", False),
    )

    roles = list(get_user_roles_with_hierarchy(user.id))

    return RegisterResponse(
        success=True,
        message="Account created successfully",
        user=AuthUser(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            roles=roles,
            created_at=user.created_at.isoformat() if getattr(user, "created_at", None) else None,
        ),
    )
