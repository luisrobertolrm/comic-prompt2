from __future__ import annotations

import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from prompt_clinica.config import settings
from prompt_clinica.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from prompt_clinica.utils.security import (
    create_access_token,
    hash_password,
    verify_password,
)

_models_dir = str(Path(__file__).resolve().parents[3] / "models")
if _models_dir not in sys.path:
    sys.path.insert(0, _models_dir)

from user import User, UserOAuth  # noqa: E402 — models/user.py


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=str(user.id),
        name=user.name,
        email=user.email,
        plan=user.plan,
    )


def register(req: RegisterRequest, db: Session) -> TokenResponse:
    existing = db.query(User).filter(User.email == req.email.lower()).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail já está em uso.",
        )

    user = User(
        name=req.name,
        email=req.email.lower(),
        password_hash=hash_password(req.password),
        terms_accepted_at=datetime.now(UTC),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        user=_user_out(user),
    )


def login(req: LoginRequest, db: Session) -> TokenResponse:
    user: User | None = (
        db.query(User).filter(User.email == req.email.lower()).first()
    )
    if (
        user is None
        or user.password_hash is None
        or not verify_password(req.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada.",
        )

    expires = settings.jwt_remember_expire_minutes if req.remember else None
    return TokenResponse(
        access_token=create_access_token(str(user.id), expires),
        user=_user_out(user),
    )


def oauth_guest(db: Session) -> TokenResponse:
    guest_uid = str(uuid.uuid4())
    user = User(
        name="Convidado",
        email=None,
        password_hash=None,
    )
    db.add(user)
    db.flush()

    oauth = UserOAuth(user_id=user.id, provider="guest", provider_uid=guest_uid)
    db.add(oauth)
    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        user=_user_out(user),
    )


def request_password_reset(email: str, db: Session) -> None:
    """Sempre retorna sem revelar se o e-mail existe."""
    user: User | None = db.query(User).filter(User.email == email.lower()).first()
    if user is None:
        return
    # TODO: gerar PasswordResetToken e enviar e-mail
