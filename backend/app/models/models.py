"""SQLAlchemy ORM models."""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id       = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email    = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Portfolio(Base):
    __tablename__ = "portfolio"
    id     = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    amount = Column(Float, nullable=False)
    price  = Column(Float, nullable=False)
    user_id = Column(Integer, nullable=False)
