import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.db.models import AllowedEmail, Shipment, User, UserSession
from app.deps import get_admin_user
from app.schemas.admin import AddAllowedEmailRequest, AllowedEmailOut
from app.schemas.user import UserOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/allowed-emails", response_model=list[AllowedEmailOut])
async def list_allowed_emails(admin: UserOut = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """List all whitelisted client emails (admin only)."""
    result = await db.execute(select(AllowedEmail).order_by(AllowedEmail.created_at.desc()))
    return result.scalars().all()


@router.post("/allowed-emails", response_model=AllowedEmailOut)
async def add_allowed_email(
    payload: AddAllowedEmailRequest,
    admin: UserOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Add an email to the whitelist (admin only)."""
    email_lower = payload.email.lower().strip()
    if not email_lower or "@" not in email_lower:
        raise HTTPException(status_code=400, detail="Please enter a valid email address")

    existing = (await db.execute(select(AllowedEmail).where(AllowedEmail.email == email_lower))).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail=f"{email_lower} is already on the whitelist")

    entry = AllowedEmail(
        email=email_lower,
        note=payload.note or "",
        added_by=admin.user_id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    logger.info(f"Admin {admin.email} added {email_lower} to whitelist")
    return entry


@router.delete("/allowed-emails/{entry_id}")
async def remove_allowed_email(
    entry_id: str,
    admin: UserOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove an email from the whitelist (admin only). User must re-add the email to allow access again."""
    entry = await db.get(AllowedEmail, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Whitelist entry not found")

    await db.delete(entry)
    await db.commit()

    logger.info(f"Admin {admin.email} removed entry {entry_id} from whitelist")
    return {"success": True}


@router.get("/users")
async def list_registered_users(admin: UserOut = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """List all registered users with their last activity (admin only)."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()

    output = []
    for u in users:
        count = (
            await db.execute(select(func.count()).select_from(Shipment).where(Shipment.user_id == u.user_id))
        ).scalar_one()
        output.append({
            "user_id": u.user_id,
            "email": u.email,
            "name": u.name,
            "picture": u.picture,
            "is_admin": u.is_admin,
            "created_at": u.created_at,
            "shipment_count": count,
        })
    return output


@router.delete("/users/{user_id}")
async def revoke_user(
    user_id: str,
    admin: UserOut = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke a user's access (delete user + sessions). Their email must also be removed from the whitelist to fully block them."""
    if user_id == admin.user_id:
        raise HTTPException(status_code=400, detail="You cannot revoke your own access")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_admin:
        raise HTTPException(status_code=400, detail="Cannot revoke another admin")

    email = user.email
    sessions = (await db.execute(select(UserSession).where(UserSession.user_id == user_id))).scalars().all()
    for s in sessions:
        await db.delete(s)
    await db.delete(user)
    await db.commit()

    logger.info(f"Admin {admin.email} revoked user {email}")
    return {"success": True, "message": f"User {email} has been signed out. Remove their email from the whitelist to prevent re-signup."}
