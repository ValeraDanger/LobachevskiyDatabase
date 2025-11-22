from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Iterable
import bcrypt
import jwt

from utils.config import (
    ACCESS_TOKEN_EXPIRES_MINUTES,
    REFRESH_TOKEN_EXPIRES_DAYS,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
)


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), password_hash.encode("utf-8"))


def _build_payload(
    sub: str, token_type: str, jti: str, exp_delta: timedelta
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {
        "sub": sub,
        "type": token_type,
        "jti": jti,
        "iat": now,
        "exp": now + exp_delta,
    }


def create_access_token(user_id: str, jti: str) -> str:
    payload = _build_payload(
        user_id,
        "access",
        jti,
        timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES),
    )
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str, jti: str) -> str:
    payload = _build_payload(
        user_id,
        "refresh",
        jti,
        timedelta(days=REFRESH_TOKEN_EXPIRES_DAYS),
    )
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])


def has_document_access(
    user_levels: Iterable[str],
    doc_levels: Iterable[str],
) -> bool:
    """
    Документ доступен, если ВСЕ его уровни доступа
    содержатся в уровнях пользователя
    """
    user_set = set(user_levels or [])
    doc_set = set(doc_levels or [])
    return doc_set.issubset(user_set)
