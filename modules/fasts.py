from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, ValidationError, validator

from fastapi import Depends, APIRouter, HTTPException

from ..database.database import DBFast
from ..dependencies import get_db

router = APIRouter()


class FastBase(BaseModel):
    pass


class FastCreate(FastBase):
    '''
    Create fast by sending start time and one of the planned duration (in hours) or planned end date
    information in the message body. 
    '''
    start_time: datetime = datetime.utcnow()
    planned_duration: Optional[float] = 23
    planned_end_time: Optional[datetime] = start_time + timedelta(hours=23)

    @validator('start_time')
    def future_date(cls, dt):
        now = datetime.utcnow()
        if dt > now:
            raise ValueError ("You can't create future date fast.")
        return dt


class Fast(FastBase):
    id: int
    user_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    completed: Optional[bool]
    duration: Optional[timedelta]
    planned_end_time: datetime
    planned_duration: Optional[float]

    class Config:
        orm_mode = True

class FastEnd(FastBase):
    end_time: Optional[datetime] = datetime.utcnow()

    @validator('end_time')
    def future_date(cls, dt):
        now = datetime.utcnow()
        if dt > now:
            raise ValueError ("You can't end fast with future date.")
        return dt


def get_fasts(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(DBFast).filter(DBFast.user_id == user_id).offset(skip).limit(limit).all()


def get_active_fast(db: Session, user_id: int):
    return db.query(DBFast).filter(DBFast.user_id == user_id, 
        DBFast.completed == False).first()


def create_user_fast(db: Session, fast: FastCreate, user_id: int):
    if fast.planned_duration:
        fast.planned_end_time = fast.start_time + timedelta(hours=fast.planned_duration)
    if not fast.planned_duration:
        fast.planned_duration = (fast.planned_end_time - fast.start_time).seconds / 3600
        print(fast.planned_duration)

    db_fast = DBFast(**fast.dict(), user_id=user_id, deleted = False,
    completed = False)
    db.add(db_fast)
    db.commit()
    db.refresh(db_fast)
    return db_fast


def end_user_fast(db: Session, fast: FastEnd, active_fast):
    active_fast.end_time = fast.end_time
    active_fast.completed = True
    active_fast.duration = active_fast.end_time - active_fast.start_time
    db.commit()
    db.refresh(active_fast)
    return active_fast


@router.post("/{user_id}/fasts/", response_model=Fast)
def create_fast_for_user(
    user_id: int, fast: FastCreate, db: Session = Depends(get_db)
):
    '''
    Creates a new fast for the active user either with planned end time (UTC without 
    timezone) or planned duration(in hours).
    If both parameters are present, planned duration wins. If none of them specified,
    default is 23 hours.
    '''
    active_fast = get_active_fast(db, user_id=user_id)
    if active_fast:
        raise HTTPException(status_code=400, detail="Already a fast is in progress")
    if fast.planned_end_time < fast.start_time:
        raise HTTPException(status_code=400, detail="End time can't be before start time")
    return create_user_fast(db=db, fast=fast, user_id=user_id)


@router.post("/{user_id}/end_fast/", response_model=Fast)
def end_fast_for_user(
    user_id: int, fast: FastEnd, db: Session = Depends(get_db)
):
    active_fast = get_active_fast(db, user_id=user_id)
    if not active_fast:
        raise HTTPException(status_code=400, detail="There is no fast is in progress")
    if fast.end_time < active_fast.start_time:
        raise HTTPException(status_code=400, detail="End date cannnot be before start date.")
    return end_user_fast(db=db, fast=fast, active_fast=active_fast)


@router.get("/{user_id}/fasts/", response_model=List[Fast])
def read_fasts(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    all_fasts = get_fasts(db, user_id=user_id, skip=skip, limit=limit)
    return all_fasts