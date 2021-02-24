from sqlalchemy.orm import Session
from typing import List, Optional
import datetime
from pydantic import BaseModel

from ..database import database as db_models
from ..modules import fasts

# schemas
class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    weight: Optional[float] = None
    height: Optional[float] = None
    active_fast: Optional[fasts.Fast] = None

    class Config:
        orm_mode = True


# Get user information for dashboard/profile page
def get_user(db: Session, user_id: int):
    user: User = db.query(db_models.User).filter(db_models.User.id == user_id).first()
    user.active_fast = fasts.get_active_fast(db, user_id)
    # calculate the duration but don't write it to database until fast is completed.
    if user.active_fast:
        user.active_fast.duration = datetime.datetime.utcnow() - user.active_fast.start_time
    return user


def get_user_by_email(db: Session, email: str):
    return db.query(db_models.User).filter(db_models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(db_models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate):
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = db_models.User(email=user.email, hashed_password=fake_hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
