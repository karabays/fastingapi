from typing import List

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

import modules.users as users
import modules.fasts as fasts
from database.database import SessionLocal, engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def root():
    return {"message": "what"}


@app.post("/users/", response_model=users.User)
def create_user(user: users.UserCreate, db: Session = Depends(get_db)):
    db_user = users.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return users.create_user(db=db, user=user)


@app.get("/users/", response_model=List[users.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    all_users = users.get_users(db, skip=skip, limit=limit)
    return all_users


@app.get("/users/{user_id}", response_model=users.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = users.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/users/{user_id}/fasts/", response_model=fasts.Fast)
def create_fast_for_user(
    user_id: int, fast: fasts.FastCreate, db: Session = Depends(get_db)
):
    active_fast = fasts.get_active_fast(db, user_id=user_id)
    if active_fast:
        raise HTTPException(status_code=400, detail="Already a fast is in progress")
    return fasts.create_user_fast(db=db, fast=fast, user_id=user_id)


@app.post("/users/{user_id}/end_fast/", response_model=fasts.Fast)
def end_fast_for_user(
    user_id: int, fast: fasts.FastEnd, db: Session = Depends(get_db)
):
    active_fast = fasts.get_active_fast(db, user_id=user_id)
    if not active_fast:
        raise HTTPException(status_code=400, detail="There is no fast is in progress")
    return fasts.end_user_fast(db=db, fast=fast, active_fast=active_fast)


@app.get("/users/{user_id}/fasts", response_model=List[fasts.Fast])
def read_fasts(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    all_fasts = fasts.get_fasts(db, user_id=user_id, skip=skip, limit=limit)
    return all_fasts