from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey
from app.db.base import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    vk_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    tg_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculties.id", ondelete="SET NULL"), nullable=True)

    faculty: Mapped["Faculty"] = relationship(back_populates="candidates")

