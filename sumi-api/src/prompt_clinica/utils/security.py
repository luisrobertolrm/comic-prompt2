from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from jwt.exceptions import InvalidTokenError

from prompt_clinica.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt(rounds=12)
    ).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    minutes = expires_minutes if expires_minutes is not None else settings.jwt_expire_minutes
    payload: dict[str, object] = {
        "sub": subject,
        "exp": datetime.now(UTC) + timedelta(minutes=minutes),
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


def decode_token(token: str) -> dict[str, object]:
    try:
        return jwt.decode(  # type: ignore[no-any-return]
            token, settings.jwt_secret_key, algorithms=["HS256"]
        )
    except InvalidTokenError as exc:
        raise ValueError("Token inválido ou expirado.") from exc
