from __future__ import annotations

import os
import datetime as dt
from typing import Optional, Any

from jose import jwt, JWTError
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_JWT_SECRET = os.getenv("JWT_SECRET_KEY", "").strip()
_JWT_ALG = os.getenv("JWT_ALG", "HS256").strip()
_JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))


def _get_secret() -> str:
    # Dev fallback to keep the app functional even without a configured secret.
    # For production, set `JWT_SECRET_KEY`.
    if not _JWT_SECRET:
        return "dev-secret-change-me"
    return _JWT_SECRET


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(user_id: int, email: str) -> str:
    now = dt.datetime.utcnow()
    exp = now + dt.timedelta(minutes=_JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, _get_secret(), algorithm=_JWT_ALG)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, _get_secret(), algorithms=[_JWT_ALG])


def get_user_id_from_token(token: str) -> Optional[int]:
    try:
        payload = decode_access_token(token)
        sub = payload.get("sub")
        return int(sub) if sub is not None else None
    except JWTError:
        return None

