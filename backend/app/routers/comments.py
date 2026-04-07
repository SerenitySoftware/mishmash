import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.comment import Comment
from app.schemas.comment import CommentCreate, CommentOut, CommentUpdate

router = APIRouter(prefix="/api/comments", tags=["comments"])

DEMO_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.post("", response_model=CommentOut, status_code=201)
async def create_comment(body: CommentCreate, db: AsyncSession = Depends(get_db)):
    comment = Comment(
        author_id=DEMO_USER_ID,
        target_type=body.target_type,
        target_id=body.target_id,
        parent_id=body.parent_id,
        body=body.body,
    )
    db.add(comment)
    await db.flush()
    return comment


@router.get("", response_model=list[CommentOut])
async def list_comments(
    target_type: str = Query(...),
    target_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Comment)
        .where(Comment.target_type == target_type, Comment.target_id == target_id, Comment.parent_id.is_(None))
        .options(selectinload(Comment.replies))
        .order_by(Comment.created_at.asc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.put("/{comment_id}", response_model=CommentOut)
async def update_comment(
    comment_id: uuid.UUID, body: CommentUpdate, db: AsyncSession = Depends(get_db),
):
    comment = await db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    comment.body = body.body
    await db.flush()
    return comment


@router.delete("/{comment_id}", status_code=204)
async def delete_comment(comment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    comment = await db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    await db.delete(comment)
    await db.flush()
