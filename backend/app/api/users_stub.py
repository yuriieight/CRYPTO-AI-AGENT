"""JWT auth router."""
from fastapi import APIRouter, HTTPException
from jose import jwt
from passlib.context import CryptContext
from app.schemas.auth import UserCreate, UserLogin, Token
from app.core.config import settings
import datetime

router  = APIRouter(prefix="/api/v1/users", tags=["auth"])
pwd_ctx = CryptContext(schemes=["bcrypt"])

@router.post("/register")
async def register(body: UserCreate):
    return {"msg": "registered", "username": body.username}

@router.post("/login", response_model=Token)
async def login(body: UserLogin):
    payload = {"sub": body.username,
               "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return Token(access_token=token)
