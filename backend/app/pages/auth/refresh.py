from fastapi import APIRouter, Request, Response, HTTPException
from jose import jwt, JWTError
from ...middleware.auth import create_access_token, verify_token
from ...config import settings

router = APIRouter()


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