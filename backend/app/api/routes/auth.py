from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.user import User
from passlib.hash import bcrypt


router = APIRouter()


@router.post("/login")
async def login(username: str, password: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user or (not bcrypt.verify(password, user.password_hash)):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "tg_id": user.tg_id,
        "faculty_id": user.faculty_id,
        "role": user.role,
    }

