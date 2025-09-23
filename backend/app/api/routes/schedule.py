from datetime import date, time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.timeslot import TimeSlot
from app.models.user import User


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/timeslots/{username}")
def get_timeslots(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    slots = db.query(TimeSlot).filter(TimeSlot.user_id == user.id).all()
    return [
        {
            "id": s.id,
            "slot_date": s.slot_date.isoformat(),
            "start_time": s.start_time.isoformat(),
            "end_time": s.end_time.isoformat(),
            "is_gas": s.is_gas,
        }
        for s in slots
    ]


@router.post("/timeslots/{username}")
def upsert_timeslot(username: str, slot_date: date, start: time, end: time, is_gas: bool, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    slot = (
        db.query(TimeSlot)
        .filter(TimeSlot.user_id == user.id, TimeSlot.slot_date == slot_date, TimeSlot.start_time == start)
        .first()
    )
    if not slot:
        slot = TimeSlot(user_id=user.id, slot_date=slot_date, start_time=start, end_time=end, is_gas=is_gas)
        db.add(slot)
    else:
        slot.end_time = end
        slot.is_gas = is_gas
    db.commit()
    db.refresh(slot)
    return {"id": slot.id}

