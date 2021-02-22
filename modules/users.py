from sqlalchemy.orm import Session
from typing import List, Optional
import datetime
from pydantic import BaseModel

import database.database as db_models
from modules import fasts

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
    user_fasts: List[fasts.Fast] = []

    class Config:
        orm_mode = True


# CRUD part
def get_user(db: Session, user_id: int):
    return db.query(db_models.User).filter(db_models.User.id == user_id).first()


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
