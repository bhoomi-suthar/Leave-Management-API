from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id       = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role     = Column(String)

class Leave(Base):
    __tablename__ = "leaves"
    id            = Column(Integer, primary_key=True)
    employee_name = Column(String)
    leave_type    = Column(String)
    start_date    = Column(Date)
    end_date      = Column(Date)
    reason        = Column(String)
    status        = Column(String, default="pending")
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)