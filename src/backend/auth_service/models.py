from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    password_hash = Column(String, nullable=True)
    roles = Column(String, default="user")

    sessions = relationship("Session", back_populates="user")


class Session(Base):
    __tablename__ = "sessions"

    token = Column(String, primary_key=True, index=True, default=lambda: uuid4().hex)
    user_id = Column(Integer, ForeignKey("users.id"))
    last_active = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="sessions")
