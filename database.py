from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from jose import jwt
from fastapi import HTTPException
from datetime import datetime, timedelta
from typing import Generator
import logging
import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")

DATABASE_URL = "sqlite:///./leave.db"
engine       = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
pwd_context  = CryptContext(schemes=["pbkdf2_sha256"])


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_token(data: dict):
    data["exp"] = datetime.utcnow() + timedelta(hours=2)
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

def log_action(message: str):
    logging.info(message)