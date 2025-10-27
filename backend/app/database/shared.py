from sqlalchemy.orm import Session
from .models import User, PasswordResetToken
from . import get_db_session
from datetime import datetime


def get_dashboard_metrics() -> dict:
    """Cross-table query for dashboard metrics"""
    with get_db_session() as db:
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        pending_resets = db.query(PasswordResetToken).filter(
            PasswordResetToken.used == False,
            PasswordResetToken.expires_at > datetime.utcnow()
        ).count()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "pending_resets": pending_resets
        }


def get_user_by_id(user_id: int) -> User | None:
    """Get user by ID"""
    with get_db_session() as db:
        return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(email: str) -> User | None:
    """Get user by email"""
    with get_db_session() as db:
        return db.query(User).filter(User.email == email).first()


def create_user(email: str, hashed_password: str) -> User:
    """Create a new user"""
    with get_db_session() as db:
        user = User(email=email, hashed_password=hashed_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user