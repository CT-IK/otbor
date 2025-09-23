from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, ForeignKey
from app.db.base import Base
from typing import Optional


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tg_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    faculty_id: Mapped[int | None] = mapped_column(ForeignKey("faculties.id", ondelete="SET NULL"), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="interviewer", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    timeslots: Mapped[list["TimeSlot"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    faculty: Mapped[Optional["Faculty"]] = relationship(back_populates="users")

