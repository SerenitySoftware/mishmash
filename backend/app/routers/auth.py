from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import TokenOut, UserLogin, UserOut, UserRegister, UserUpdate
from app.services.auth import authenticate_user, create_access_token, register_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
async def register(body: UserRegister, db: AsyncSession = Depends(get_db)):
    try:
        user = await register_user(
            db, email=body.email, username=body.username,
            name=body.name, password=body.password,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    token = create_access_token(user.id)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, email=body.email, password=body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token(user.id)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    return user


@router.put("/me", response_model=UserOut)
async def update_me(
    body: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.name is not None:
        user.name = body.name
    if body.bio is not None:
        user.bio = body.bio
    if body.avatar_url is not None:
        user.avatar_url = body.avatar_url
    await db.flush()
    return user
