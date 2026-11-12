import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from user import User

from prompt_clinica.database import get_db
from prompt_clinica.deps import get_current_admin
from prompt_clinica.schemas.app_settings import AppSettingsOut, AppSettingsValues
from prompt_clinica.schemas.auth import PendingUserOut
from prompt_clinica.services import app_settings_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users/pending", response_model=list[PendingUserOut])
def list_pending_users(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> list[PendingUserOut]:
    users = (
        db.query(User)
        .filter(User.approved.is_(False))
        .order_by(User.created_at)
        .all()
    )
    return [
        PendingUserOut(id=str(u.id), name=u.name, email=u.email, created_at=u.created_at)
        for u in users
    ]


@router.post("/users/{user_id}/approve", status_code=204)
def approve_user(
    user_id: uuid.UUID,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> None:
    user: User | None = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    user.approved = True
    db.commit()


@router.delete("/users/{user_id}", status_code=204)
def reject_user(
    user_id: uuid.UUID,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> None:
    user: User | None = (
        db.query(User).filter(User.id == user_id, User.approved.is_(False)).first()
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    db.delete(user)
    db.commit()


@router.get("/app-settings", response_model=AppSettingsOut)
def get_app_settings(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AppSettingsOut:
    return app_settings_service.get_app_settings(db)


@router.put("/app-settings", response_model=AppSettingsOut)
def update_app_settings(
    data: AppSettingsValues,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AppSettingsOut:
    return app_settings_service.update_app_settings(data, db)
