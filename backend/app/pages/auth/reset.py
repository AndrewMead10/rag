from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from secrets import token_urlsafe

from ...database import get_db_session
from ...database.models import User, PasswordResetToken
from ...database.shared import get_user_by_email
from ...middleware.auth import get_password_hash
from ...functions.email import email_service
from ...config import settings


router = APIRouter()


class ResetRequest(BaseModel):
    email: EmailStr


class ResetConfirm(BaseModel):
    token: str
    new_password: str


@router.post("/auth/reset/onsubmit/request")
async def request_password_reset(payload: ResetRequest):
    if not settings.enable_password_reset:
        raise HTTPException(status_code=403, detail="Password reset is disabled")

    user = get_user_by_email(payload.email)

    # Always respond success to avoid user enumeration
    if not user:
        return {"success": True, "message": "If an account exists, a reset email has been sent"}

    token = token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)

    with get_db_session() as db:
        prt = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at,
            used=False,
            active=True,
        )
        db.add(prt)
        db.commit()

    email_service.send_password_reset(user.email, token)
    return {"success": True, "message": "If an account exists, a reset email has been sent"}


@router.post("/auth/reset/onsubmit/confirm")
async def confirm_password_reset(payload: ResetConfirm):
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    with get_db_session() as db:
        prt = db.query(PasswordResetToken).filter(PasswordResetToken.token == payload.token).first()
        if not prt or not prt.active or prt.used or (prt.expires_at and prt.expires_at < datetime.utcnow()):
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        user = db.query(User).filter(User.id == prt.user_id).first()
        if not user:
            raise HTTPException(status_code=400, detail="Invalid token")

        user.hashed_password = get_password_hash(payload.new_password)
        prt.used = True
        prt.active = False
        db.commit()

    return {"success": True, "message": "Password has been reset"}

