from typing import List

import uvicorn

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from sqlalchemy.orm import Session

from .modules import users
from .modules import fasts
from .database import database
from . import config


database.Base.metadata.create_all(bind=database.engine)


app = FastAPI(
    title=config.title,
    description=config.description,
    version=config.version,
    openapi_tags=config.tags_metadata
)

app.include_router(fasts.router, prefix="/fast", tags=["fasts"])
app.include_router(users.router, prefix="/users", tags=['users'])


@app.get("/")
def root():
    return {"message": "what"}