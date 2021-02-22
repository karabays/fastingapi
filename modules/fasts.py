from sqlalchemy.orm import Session
from typing import List, Optional
import datetime
from pydantic import BaseModel

import database.database as db_models


class FastBase(BaseModel):
    start_time: datetime.datetime
    planned_duration: int


# Shcema for creating the fasts, nothing in there because inheriting from 
# FastBase Class
class FastCreate(FastBase):
    pass


# The Schema for returning the fasts. I don't need to add start_time and 
# planned duration because already inheriting them from FastBase class.
class Fast(FastBase):
    id: int
    user_id: int
    end_time: Optional[datetime.datetime] = None

    class Config:
        orm_mode = True


def get_fasts(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(db_models.Fast).filter(db_models.Fast.user_id == user_id).offset(skip).limit(limit).all()


def get_active_fast(db: Session, user_id: int):
    return db.query(db_models.Fast).filter(db_models.Fast.user_id == user_id, 
        db_models.Fast.completed == False).first()


def create_user_fast(db: Session, fast: FastCreate, user_id: int):
    db_fast = db_models.Fast(**fast.dict(), user_id=user_id, deleted = False,
    completed = False, active = True)
    db.add(db_fast)
    db.commit()
    db.refresh(db_fast)
    return db_fast


# this has to be a post request. also needs a FastEnd class with 
# optional end date. if end date is empty, then use now...
def end_user_fast(db: Session, user_id: int, id: int):
    db_fast = db.query(db_models.Fast).filter(db_models.Fast.id == id).first()
    db_fast.completed = True
    db.commit()
    db.refresh(db_fast)
    return db_fast