from sqlalchemy.orm import Session
from typing import List, Optional
import datetime
from pydantic import BaseModel

from fastapi import Depends, APIRouter, HTTPException

from ..database.database import DBUser
from ..modules import fasts, weights
from ..dependencies import get_db

router = APIRouter()

# schemas
class UserBase(BaseModel):
    email: str
    weight: Optional[float]
    height: Optional[float]
    goal_weight: Optional[float]
    unit: weights.MeasurementSys = weights.MeasurementSys.metric

    class Config:
        orm_mode = True

class UserCreate(UserBase):
    password: str

class UserStats(BaseModel):
    number_of_fasts: int
    total_hours_fasted: float
    longest_fast: float
    weight: float
    height: float
    bmi: float
    goal_weight: float
    start_weight: float
    weight_loss: float


class User(UserBase):
    id: int
    is_active: bool
    weight: Optional[float] = None
    height: Optional[float] = None
    active_fast: Optional[fasts.Fast] = None
    user_stats: Optional[UserStats] = None


# Get user information for dashboard/profile page
def get_user(db: Session, user_id: int):
    user: User = db.query(DBUser).filter(DBUser.id == user_id).first()
    user.active_fast = fasts.get_active_fast(db, user_id)
    # calculate the duration but don't write it to database until fast is completed.
    if user.active_fast:
        user.active_fast.duration = datetime.datetime.now() - user.active_fast.start_time
    return user


def get_user_by_email(db: Session, email: str):
    # print(db.query(db_models.DBUser).filter(db_models.DBUser.email == email).first())
    return db.query(DBUser).filter(DBUser.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(DBUser).offset(skip).limit(limit).all()


def create_user_db(db: Session, user: UserCreate):
    user_dict = user.dict()
    user_dict['hashed_password'] = user.password + "notreallyhashed"
    user_dict.pop('password')
    db_user = DBUser(**user_dict)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/", response_model=UserBase)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user.
    """
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return create_user_db(db=db, user=user)


@router.get("/", response_model=List[User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get list of all users.
    """
    all_users = get_users(db, skip=skip, limit=limit)
    return all_users


@router.get("/{user_id}", response_model=User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """Get details of a specific user.
    """
    db_user = get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user