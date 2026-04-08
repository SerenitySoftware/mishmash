"""Notification creation helpers."""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


async def notify(
    db: AsyncSession,
    user_id: uuid.UUID,
    type: str,
    title: str,
    body: str | None = None,
    target_type: str | None = None,
    target_id: uuid.UUID | None = None,
    actor_id: uuid.UUID | None = None,
    meta: dict | None = None,
) -> Notification:
    """Create a notification for a user."""
    n = Notification(
        user_id=user_id,
        type=type,
        title=title,
        body=body,
        target_type=target_type,
        target_id=target_id,
        actor_id=actor_id,
        meta=meta,
    )
    db.add(n)
    await db.flush()
    return n


async def notify_comment(
    db: AsyncSession,
    target_owner_id: uuid.UUID,
    commenter_name: str,
    target_type: str,
    target_id: uuid.UUID,
    target_name: str,
    actor_id: uuid.UUID,
) -> Notification | None:
    """Notify content owner when someone comments."""
    if target_owner_id == actor_id:
        return None  # Don't notify yourself
    return await notify(
        db,
        user_id=target_owner_id,
        type="comment",
        title=f"{commenter_name} commented on your {target_type}",
        body=f'New comment on "{target_name}"',
        target_type=target_type,
        target_id=target_id,
        actor_id=actor_id,
    )


async def notify_star(
    db: AsyncSession,
    target_owner_id: uuid.UUID,
    starrer_name: str,
    target_type: str,
    target_id: uuid.UUID,
    target_name: str,
    actor_id: uuid.UUID,
) -> Notification | None:
    if target_owner_id == actor_id:
        return None
    return await notify(
        db,
        user_id=target_owner_id,
        type="star",
        title=f"{starrer_name} starred your {target_type}",
        body=f'"{target_name}" received a new star',
        target_type=target_type,
        target_id=target_id,
        actor_id=actor_id,
    )


async def notify_fork(
    db: AsyncSession,
    target_owner_id: uuid.UUID,
    forker_name: str,
    target_type: str,
    target_id: uuid.UUID,
    target_name: str,
    actor_id: uuid.UUID,
) -> Notification | None:
    if target_owner_id == actor_id:
        return None
    return await notify(
        db,
        user_id=target_owner_id,
        type="fork",
        title=f"{forker_name} forked your {target_type}",
        body=f'"{target_name}" was forked',
        target_type=target_type,
        target_id=target_id,
        actor_id=actor_id,
    )


async def notify_run_completed(
    db: AsyncSession,
    user_id: uuid.UUID,
    analysis_title: str,
    analysis_id: uuid.UUID,
    status: str,
) -> Notification:
    return await notify(
        db,
        user_id=user_id,
        type=f"run_{status}",
        title=f"Analysis run {status}: {analysis_title}",
        target_type="analysis",
        target_id=analysis_id,
    )
