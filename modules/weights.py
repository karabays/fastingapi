from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, ValidationError, validator
from enum import Enum

from fastapi import Depends, APIRouter, HTTPException

from ..database.database import DBWeight
from ..dependencies import get_db

router = APIRouter()

class MeasurementSys(str, Enum):
    metric = 'metric'
    imperial = 'imperial'

class WeightBase(BaseModel):
    weight: float
    weight_time: datetime = datetime.utcnow()
    unit: MeasurementSys = MeasurementSys.metric

    class Config:
        orm_mode = True

class Weight(WeightBase):
    bmi: float


def user_weight_in(db: Session, weight: Weight, user_id: int):
    if weight.unit == MeasurementSys.imperial:
        weight.weight = weight.weight * 0.45359237
        weight.unit = 'kgs'
    db_weight = DBWeight(**weight.dict(), user_id=user_id)
    db_weight.bmi = calculate_bmi(weight)
    db.add(db_weight)
    db.commit()
    db.refresh(db_weight)
    return db_weight


def calculate_bmi(weight: Weight):
    return weight.weight / 1.72 ** 2

@router.post("/{user_id}/fasts/", response_model=Weight)
def new_weight_for_user(user_id: int, weight: WeightBase, db: Session = Depends(get_db)):
    ''' New weight entry for the user. Send metric for kgs and imperial for lbs.
    '''
    return user_weight_in(db=db, weight=weight, user_id=user_id)