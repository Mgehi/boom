import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.base import get_db
from app.db.models import AllowedEmail, User, UserSession
from app.deps import get_current_user
from app.schemas.user import UserOut
from app.services.google_oauth import oauth

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_KWARGS = dict(path="/", httponly=True, secure=True, samesite="none")


@router.get("/google/login")
async def google_login(request: Request):
    """Redirect the browser to Google's consent screen."""
    return await oauth.google.authorize_redirect(request, settings.GOOGLE_REDIRECT_URI)


@router.get("/google/callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """Exchange the Google auth code for the user's profile, apply the
    admin-bootstrap / whitelist rules, and start a session."""
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        logger.error(f"Google OAuth exchange failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Google sign-in failed")

    userinfo = token.get("userinfo")
    if not userinfo or not userinfo.get("email"):
        raise HTTPException(status_code=401, detail="Invalid auth response")

    email = userinfo["email"]
    name = userinfo.get("name", "")
    picture = userinfo.get("picture", "")
    email_lower = email.lower().strip()
    now = datetime.now(timezone.utc)

    admin_exists = (await db.execute(select(User).where(User.is_admin.is_(True)))).scalars().first()
    existing = (await db.execute(select(User).where(User.email == email_lower))).scalars().first()

    if existing:
        user_id = existing.user_id
        is_admin = existing.is_admin
        if not admin_exists and not is_admin:
            existing.is_admin = True
            is_admin = True
            logger.info(f"Bootstrap: promoted {email_lower} to admin (first user)")
        existing.name = name
        existing.picture = picture
    else:
        is_admin = False
        if not admin_exists:
            is_admin = True
            logger.info(f"Bootstrap: making {email_lower} the first admin")
        else:
            allowed = (await db.execute(select(AllowedEmail).where(AllowedEmail.email == email_lower))).scalars().first()
            if not allowed:
                logger.warning(f"Access denied for unwhitelisted email: {email_lower}")
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied. The email '{email}' is not authorized to use this dashboard. Please contact your administrator."
                )

        user_id = f"user_{uuid.uuid4().hex[:12]}"
        db.add(User(user_id=user_id, email=email_lower, name=name, picture=picture, is_admin=is_admin, created_at=now))

    session_token = secrets.token_urlsafe(32)
    expires_at = now + timedelta(days=7)
    db.add(UserSession(session_token=session_token, user_id=user_id, expires_at=expires_at, created_at=now))
    await db.commit()

    response = RedirectResponse(url=settings.FRONTEND_URL)
    response.set_cookie(key="session_token", value=session_token, max_age=7 * 24 * 60 * 60, **COOKIE_KWARGS)
    return response


@router.get("/me", response_model=UserOut)
async def get_me(current_user: UserOut = Depends(get_current_user)):
    """Get the current authenticated user."""
    return current_user


@router.post("/logout")
async def logout(response: Response, request: Request, db: AsyncSession = Depends(get_db)):
    """Logout user - delete session and clear cookie."""
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if token:
        session = await db.get(UserSession, token)
        if session:
            await db.delete(session)
            await db.commit()

    response.delete_cookie(key="session_token", path="/", samesite="none", secure=True)
    return {"success": True}
