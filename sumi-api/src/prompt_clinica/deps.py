from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from user import User

import prompt_clinica._paths  # noqa: F401
from prompt_clinica.database import get_db
from prompt_clinica.utils.security import decode_token

_bearer = HTTPBearer()
_bearer_optional = HTTPBearer(auto_error=False)


def get_current_user_optional(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer_optional),
    db: Session = Depends(get_db),
) -> User | None:
    if creds is None:
        return None
    try:
        payload = decode_token(creds.credentials)
        user_id = uuid.UUID(str(payload["sub"]))
    except (ValueError, KeyError):
        return None
    user: User | None = (
        db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    )
    if user is None or not user.approved:
        return None
    return user


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_token(creds.credentials)
        user_id = uuid.UUID(str(payload["sub"]))
    except (ValueError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido.")

    user: User | None = (
        db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado.")
    if not user.approved:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Conta aguardando aprovação.")
    return user


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if user.group.type != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito ao administrador.")
    return user
