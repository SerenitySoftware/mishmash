import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.notification import Notification
from app.models.user import User

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationOut(BaseModel):
    id: uuid.UUID
    type: str
    title: str
    body: str | None
    is_read: bool
    target_type: str | None
    target_id: uuid.UUID | None
    actor_id: uuid.UUID | None
    created_at: str

    model_config = {"from_attributes": True}


class NotificationsListOut(BaseModel):
    items: list[NotificationOut]
    unread_count: int
    total: int


@router.get("", response_model=NotificationsListOut)
async def list_notifications(
    unread_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    base = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        base = base.where(Notification.is_read == False)  # noqa: E712

    total = (await db.execute(
        select(func.count()).select_from(Notification).where(Notification.user_id == user.id)
    )).scalar()
    unread_count = (await db.execute(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == user.id, Notification.is_read == False  # noqa: E712
        )
    )).scalar()

    stmt = base.order_by(Notification.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(stmt)).scalars().all()

    return NotificationsListOut(items=items, unread_count=unread_count, total=total)


@router.post("/{notification_id}/read", status_code=200)
async def mark_read(
    notification_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    n = await db.get(Notification, notification_id)
    if not n or n.user_id != user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.is_read = True
    await db.flush()
    return {"ok": True}


@router.post("/read-all", status_code=200)
async def mark_all_read(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == user.id, Notification.is_read == False)  # noqa: E712
        .values(is_read=True)
    )
    await db.flush()
    return {"ok": True}


@router.get("/unread-count")
async def unread_count(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = (await db.execute(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == user.id, Notification.is_read == False  # noqa: E712
        )
    )).scalar()
    return {"unread_count": count}
