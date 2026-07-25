from datetime import datetime, timezone
from typing import Optional

from fastapi import Cookie, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.db.models import User as UserModel, UserSession
from app.schemas.user import UserOut


async def get_current_user(
    request: Request,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """Get the current authenticated user from cookie or Authorization header."""
    token = session_token
    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(
        select(UserSession, UserModel)
        .join(UserModel, UserModel.user_id == UserSession.user_id)
        .where(UserSession.session_token == token)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid session")
    session, user = row

    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")

    return UserOut.model_validate(user)


async def get_admin_user(current_user: UserOut = Depends(get_current_user)) -> UserOut:
    """Require admin privileges."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
