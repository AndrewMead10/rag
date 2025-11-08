from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from secrets import token_urlsafe
from .me import UserResponse as AuthUser
from ...middleware.auth import (
    get_password_hash,
    create_access_token,
    create_refresh_token,
    get_user_roles_with_hierarchy,
)
from ...database.shared import get_user_by_email, create_user
from ...database import get_db_session
from ...functions.email import email_service
from ...config import settings

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    success: bool
    message: str


@router.post("/auth/register/onsubmit", response_model=RegisterResponse)
async def register_onsubmit(user_data: RegisterRequest, response: Response):
    """Handle user registration with email verification"""
    if not settings.enable_user_registration:
        raise HTTPException(status_code=403, detail="Registration is disabled")

    existing_user = get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    if len(user_data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    hashed_password = get_password_hash(user_data.password)
    try:
        user = create_user(user_data.email, hashed_password)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Generate verification token
    verification_token = token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=24)

    # Store verification token in database
    with get_db_session() as db:
        db_user = db.query(type(user)).filter_by(id=user.id).first()
        if db_user:
            db_user.email_verification_token = verification_token
            db_user.email_verification_token_expires_at = expires_at
            db.commit()

    # Send verification email
    email_service.send_email_verification(user.email, verification_token)

    return RegisterResponse(
        success=True,
        message="Registration successful! Please check your email to verify your account.",
    )
