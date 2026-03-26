from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, field_validator
from typing import Dict, Any

from database import db_fetchone, db_execute
from services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_user_id_from_token,
)


router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class RegisterRequest(BaseModel):
    email: str
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if "@" not in v or "." not in v:
            raise ValueError("invalid email")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if "@" not in v or "." not in v:
            raise ValueError("invalid email")
        return v


def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    user_id = get_user_id_from_token(token)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db_fetchone("SELECT id, email FROM users WHERE id=?", (user_id,))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest):
    existing = db_fetchone("SELECT id FROM users WHERE email=?", (req.email.lower(),))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    password_hash = hash_password(req.password)
    db_execute(
        "INSERT INTO users (email, password_hash) VALUES (?,?)",
        (req.email.lower(), password_hash),
    )
    return {"success": True, "data": {"registered": True}, "error": None}


@router.post("/auth/login")
def login(req: LoginRequest):
    user = db_fetchone(
        "SELECT id, email, password_hash FROM users WHERE email=?",
        (req.email.lower(),),
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(req.password, user.get("password_hash") or ""):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(user_id=int(user["id"]), email=str(user["email"]))
    return {
        "success": True,
        "data": {"access_token": token, "token_type": "bearer"},
        "error": None,
    }


@router.get("/auth/me")
def me(user: Dict[str, Any] = Depends(get_current_user)):
    return {"success": True, "data": user, "error": None}

