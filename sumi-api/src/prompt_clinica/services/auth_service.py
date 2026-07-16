from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from prompt_clinica.config import settings
from prompt_clinica.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
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

from user import Group, User  # noqa: E402 — models/user.py


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=str(user.id),
        name=user.name,
        email=user.email,
        plan=user.plan,
        group=user.group.type,
        approved=user.approved,
    )


def register(req: RegisterRequest, db: Session) -> RegisterResponse:
    existing = db.query(User).filter(User.email == req.email.lower()).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail já está em uso.",
        )

    padrao = db.query(Group).filter(Group.type == "padrao").first()
    user = User(
        name=req.name,
        email=req.email.lower(),
        password_hash=hash_password(req.password),
        terms_accepted_at=datetime.now(UTC),
        group_id=padrao.id,
        approved=False,
    )
    db.add(user)
    db.commit()

    return RegisterResponse(
        detail="Conta criada! Aguarde a aprovação do administrador para entrar."
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
    if not user.approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sua conta ainda não foi aprovada pelo administrador.",
        )

    expires = settings.jwt_remember_expire_minutes if req.remember else None
    return TokenResponse(
        access_token=create_access_token(str(user.id), expires),
        user=_user_out(user),
    )


def request_password_reset(email: str, db: Session) -> None:
    """Sempre retorna sem revelar se o e-mail existe."""
    user: User | None = db.query(User).filter(User.email == email.lower()).first()
    if user is None:
        return
    # TODO: gerar PasswordResetToken e enviar e-mail
