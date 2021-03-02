from typing import List

import uvicorn

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from sqlalchemy.orm import Session

from .modules import users
from .modules import fasts
from .database import database


database.Base.metadata.create_all(bind=database.engine)


app = FastAPI(
    title = "Fast(i)ngAPI",
    description = "Fasting and weight tracker built with FastAPI at the backend and Angular at the front."
)

app.include_router(fasts.router)
app.include_router(users.router)


@app.get("/")
def root():
    return {"message": "what"}