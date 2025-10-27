import secrets
from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from ...config import settings
from ...database.shared import create_user, get_user_by_email
from ...middleware.auth import get_password_hash, set_auth_cookies

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

router = APIRouter()


def _oauth_enabled() -> bool:
    return bool(
        settings.google_client_id
        and settings.google_client_secret
        and settings.google_redirect_uri
    )


def _cookie_secure_flag() -> bool:
    secure = bool(getattr(settings, "cookie_secure", False))
    if not secure:
        secure = settings.frontend_url.startswith("https://")
    return secure


def _sanitize_redirect(redirect: Optional[str]) -> str:
    if not redirect or not redirect.startswith("/"):
        return "/dashboard"
    return redirect


@router.get("/auth/google/login")
async def google_login(redirect: Optional[str] = None):
    """Initiate Google OAuth flow"""
    if not _oauth_enabled():
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")

    state = secrets.token_urlsafe(32)
    redirect_path = _sanitize_redirect(redirect)

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }

    redirect_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    response = RedirectResponse(url=redirect_url, status_code=302)

    response.set_cookie(
        "google_oauth_state",
        state,
        httponly=True,
        max_age=600,
        samesite="lax",
        secure=_cookie_secure_flag(),
    )
    response.set_cookie(
        "google_oauth_redirect",
        redirect_path,
        httponly=True,
        max_age=600,
        samesite="lax",
        secure=_cookie_secure_flag(),
    )

    return response


@router.get("/auth/google/callback")
async def google_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    """Handle Google OAuth callback"""
    if not _oauth_enabled():
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")

    if error:
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {error}")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    state_cookie = request.cookies.get("google_oauth_state")
    if not state_cookie or state_cookie != state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    redirect_path = _sanitize_redirect(request.cookies.get("google_oauth_redirect"))

    token_payload = {
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.google_redirect_uri,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        token_response = await client.post(GOOGLE_TOKEN_URL, data=token_payload)

    if token_response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to exchange code: {token_response.text}",
        )

    token_data = token_response.json()
    access_token = token_data.get("access_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="Missing access token from Google")

    async with httpx.AsyncClient(timeout=10) as client:
        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if userinfo_response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch user info: {userinfo_response.text}",
        )

    userinfo = userinfo_response.json()
    email = userinfo.get("email")
    email_verified = userinfo.get("email_verified", False)

    if not email or not email_verified:
        raise HTTPException(
            status_code=400, detail="Google account email is not verified"
        )

    if settings.google_allowed_domains:
        domain = email.split("@")[-1].lower()
        allowed = {d.lower() for d in settings.google_allowed_domains}
        if domain not in allowed:
            raise HTTPException(status_code=403, detail="Email domain is not permitted")

    user = get_user_by_email(email)
    if not user:
        random_secret = secrets.token_urlsafe(48)
        user = create_user(email=email, hashed_password=get_password_hash(random_secret))

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    target_url = settings.frontend_url.rstrip("/") + redirect_path
    response = RedirectResponse(url=target_url, status_code=302)

    response.delete_cookie(
        "google_oauth_state",
        path="/",
        secure=_cookie_secure_flag(),
        httponly=True,
        samesite="lax",
    )
    response.delete_cookie(
        "google_oauth_redirect",
        path="/",
        secure=_cookie_secure_flag(),
        httponly=True,
        samesite="lax",
    )

    set_auth_cookies(response, user.id)
    return response
