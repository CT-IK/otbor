from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from passlib.hash import bcrypt


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or (not bcrypt.verify(password, user.password_hash)):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "tg_id": user.tg_id,
        "faculty": user.faculty,
        "role": user.role,
    }

