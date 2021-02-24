from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, ValidationError, validator

from fastapi import Depends

from ..database import database as db_models


class FastBase(BaseModel):
    pass


# Shcema for creating the fasts, nothing in there because inheriting from 
# FastBase Class
class FastCreate(FastBase):
    '''
    Create fast by sending start time and one of the planned duration (in hours) or planned end date
    information in the message body. 
    '''
    start_time: datetime = datetime.utcnow()
    planned_end_time: datetime = datetime.utcnow() + timedelta(hours=23)

    @validator('start_time')
    def future_date(cls, dt):
        now = datetime.utcnow()
        if dt > now:
            raise ValueError ("You can't create future date fast.")
        return dt

# The Schema for returning the fasts. I don't need to add start_time and 
# planned duration because already inheriting them from FastBase class.
class Fast(FastBase):
    id: int
    user_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    completed: Optional[bool]
    duration: Optional[timedelta]
    planned_end_time: datetime

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
    return db.query(db_models.Fast).filter(db_models.Fast.user_id == user_id).offset(skip).limit(limit).all()


def get_active_fast(db: Session, user_id: int):
    return db.query(db_models.Fast).filter(db_models.Fast.user_id == user_id, 
        db_models.Fast.completed == False).first()


def create_user_fast(db: Session, fast: FastCreate, user_id: int):
    db_fast = db_models.Fast(**fast.dict(), user_id=user_id, deleted = False,
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
