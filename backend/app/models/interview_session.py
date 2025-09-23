from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, Date, Time, UniqueConstraint
from app.db.base import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"
    __table_args__ = (
        UniqueConstraint("faculty_id", "slot_date", "start_time", name="uq_faculty_date_time"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculties.id", ondelete="CASCADE"), nullable=False)
    slot_date: Mapped[Date] = mapped_column(Date, nullable=False)
    start_time: Mapped[Time] = mapped_column(Time, nullable=False)
    end_time: Mapped[Time] = mapped_column(Time, nullable=False)
    interviewer_exp_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    interviewer_new_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    candidate_id: Mapped[int | None] = mapped_column(ForeignKey("candidates.id", ondelete="SET NULL"), nullable=True)

    # Relationships (optional to navigate)

