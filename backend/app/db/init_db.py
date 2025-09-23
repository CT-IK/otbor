from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from app.models.user import User


def init_core_users(db: Session) -> None:
    if not db.query(User).filter(User.username == "user1").first():
        db.add(User(username="user1", password_hash=bcrypt.hash("password"), faculty="ФКН", role="interviewer"))
    if not db.query(User).filter(User.username == "admin").first():
        db.add(User(username="admin", password_hash=bcrypt.hash("password"), faculty="ФКН", role="admin"))
    db.commit()

