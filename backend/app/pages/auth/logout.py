from fastapi import APIRouter, Response
from ...config import settings

router = APIRouter()


@router.post("/auth/logout/onsubmit")
async def logout(response: Response):
    """Logout user by clearing cookies"""
    response.delete_cookie("access_token", samesite="lax", secure=getattr(settings, "cookie_secure", False))
    response.delete_cookie("refresh_token", samesite="lax", secure=getattr(settings, "cookie_secure", False))
    return {"message": "Logged out successfully"}
