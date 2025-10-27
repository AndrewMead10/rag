from fastapi import HTTPException, Request, Depends, Response
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from ..config import settings
from ..database.models import User, Role, UserRole
from ..database import get_db_session
from ..database.shared import get_user_by_id

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """Create an access token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_ttl_minutes)
    
    to_encode = {"sub": str(user_id), "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """Create a refresh token"""
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_ttl_days)
    to_encode = {"sub": str(user_id), "exp": expire, "type": "refresh"}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=ALGORITHM)


def set_auth_cookies(response: Response, user_id: int) -> None:
    """Set auth cookies for the provided user"""
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    secure_cookie = bool(getattr(settings, "cookie_secure", False))
    if not secure_cookie:
        secure_cookie = settings.frontend_url.startswith("https://")

    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        max_age=settings.access_token_ttl_minutes * 60,
        samesite="lax",
        secure=secure_cookie,
        path="/",
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        max_age=settings.refresh_token_ttl_days * 24 * 60 * 60,
        samesite="lax",
        secure=secure_cookie,
        path="/",
    )


def verify_token(token: str) -> bool:
    """Verify if a token is valid"""
    try:
        jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        return True
    except JWTError:
        return False


def get_current_user(request: Request) -> User:
    """Validate access token from HttpOnly cookie and load user from DB"""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        user_id: int = int(payload["sub"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


def get_user_roles_with_hierarchy(user_id: int) -> set[str]:
    """Get all roles for a user, including inherited roles from hierarchy"""
    with get_db_session() as db:
        user_roles = db.query(Role).join(UserRole).filter(UserRole.user_id == user_id).all()
        
        all_roles = set()
        for role in user_roles:
            all_roles.add(role.name)
            current = role
            while current.parent:
                current = current.parent
                all_roles.add(current.name)
        
        return all_roles


def has_permission(user_id: int, required_role: str) -> bool:
    """Check role via user_roles with hierarchy support; 'admin' overrides"""
    roles = get_user_roles_with_hierarchy(user_id)
    return required_role in roles


def require_role(required_role: str):
    """Decorator for role-based authorization with hierarchy support"""
    def role_checker(current_user: User = Depends(get_current_user)):
        if not has_permission(current_user.id, required_role):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker


def optional_user(request: Request) -> Optional[User]:
    """Get current user if authenticated, None otherwise"""
    try:
        return get_current_user(request)
    except HTTPException:
        return None
