from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, DateTime, Boolean, Interval, Float

SQLALCHEMY_DATABASE_URL = "sqlite:///fastingapi/database/fastingapi.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
session = SessionLocal()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    weight = Column(Float)
    height = Column(Float)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    fasts = relationship("Fast", back_populates="user")


class Fast(Base):
    __tablename__ = 'fasts'
    id = Column(Integer, primary_key = True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    deleted = Column(Boolean)
    completed = Column(Boolean)
    duration = Column(Interval)
    planned_end_time = Column(DateTime)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="fasts")