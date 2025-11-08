from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

from ...database import get_db_session
from ...database.models import User

router = APIRouter()


class VerifyEmailRequest(BaseModel):
    token: str


class VerifyEmailResponse(BaseModel):
    success: bool
    message: str


@router.post("/auth/verify-email/onsubmit", response_model=VerifyEmailResponse)
async def verify_email(payload: VerifyEmailRequest):
    """Handle email verification when user clicks the link"""
    with get_db_session() as db:
        user = db.query(User).filter(
            User.email_verification_token == payload.token
        ).first()

        if not user:
            raise HTTPException(status_code=400, detail="Invalid verification token")

        # Check if token has expired (24 hours)
        if user.email_verification_token_expires_at and user.email_verification_token_expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Verification token has expired")

        # Mark email as verified and clear the token
        user.is_email_verified = True
        user.email_verification_token = None
        user.email_verification_token_expires_at = None
        db.commit()

    return VerifyEmailResponse(
        success=True,
        message="Email verified successfully! You can now log in."
    )
