from sqlalchemy.orm import Session
from typing import List, Optional
import datetime
from pydantic import BaseModel, ValidationError, validator

import database.database as db_models


class FastBase(BaseModel):
    pass


# Shcema for creating the fasts, nothing in there because inheriting from 
# FastBase Class
class FastCreate(FastBase):
    start_time: datetime.datetime
    planned_duration: int
    
    @validator('start_time')
    def future_date(cls, dt):
        now = datetime.datetime.now()
        if dt > now:
            raise ValueError ("You can't create future date fast.")
        return dt

# The Schema for returning the fasts. I don't need to add start_time and 
# planned duration because already inheriting them from FastBase class.
class Fast(FastBase):
    id: int
    user_id: int
    start_time: datetime.datetime
    end_time: Optional[datetime.datetime] = None
    completed: Optional[bool]
    planned_duration: Optional[int]
    duration: Optional[int]


    class Config:
        orm_mode = True

class FastEnd(FastBase):
    end_time: Optional[datetime.datetime] = datetime.datetime.now()

    @validator('end_time')
    def future_date(cls, dt):
        now = datetime.datetime.now()
        if dt > now:
            raise ValueError ("You can't create future date fast.")
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
    db.commit()
    db.refresh(active_fast)
    return active_fast
