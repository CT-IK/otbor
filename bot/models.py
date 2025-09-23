from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tg_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    faculty_id: Mapped[int | None]
    role: Mapped[str] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean)

