from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String
from app.db.base import Base


class Faculty(Base):
    __tablename__ = "faculties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="faculty")
    candidates: Mapped[list["Candidate"]] = relationship(back_populates="faculty")

