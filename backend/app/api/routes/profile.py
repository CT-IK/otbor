from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.user import User


router = APIRouter()


@router.post("/profile")
async def update_profile(username: str, full_name: str, tg_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.full_name = full_name
    user.tg_id = tg_id
    await db.merge(user)
    await db.commit()
    await db.refresh(user)
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "tg_id": user.tg_id,
        "faculty_id": user.faculty_id,
        "role": user.role,
    }

