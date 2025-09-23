from datetime import date, time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.timeslot import TimeSlot
from app.models.user import User


router = APIRouter()


@router.get("/timeslots/{username}")
async def get_timeslots(username: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    slots = (await db.execute(select(TimeSlot).where(TimeSlot.user_id == user.id))).scalars().all()
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
async def upsert_timeslot(
    username: str,
    slot_date: date,
    start: time,
    end: time,
    is_gas: bool,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    slot_result = await db.execute(
        select(TimeSlot).where(
            TimeSlot.user_id == user.id, TimeSlot.slot_date == slot_date, TimeSlot.start_time == start
        )
    )
    slot = slot_result.scalar_one_or_none()
    if not slot:
        slot = TimeSlot(user_id=user.id, slot_date=slot_date, start_time=start, end_time=end, is_gas=is_gas)
        db.add(slot)
    else:
        slot.end_time = end
        slot.is_gas = is_gas
    await db.commit()
    await db.refresh(slot)
    return {"id": slot.id}

