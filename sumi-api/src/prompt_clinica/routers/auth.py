from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from prompt_clinica.database import get_db
from prompt_clinica.schemas.auth import (
    LoginRequest,
    PasswordResetRequest,
    RegisterRequest,
    TokenResponse,
)
from prompt_clinica.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201, response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return auth_service.register(req, db)


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return auth_service.login(req, db)


@router.post("/oauth/guest", response_model=TokenResponse)
def oauth_guest(db: Session = Depends(get_db)) -> TokenResponse:
    return auth_service.oauth_guest(db)


@router.post("/password-reset/request", status_code=202)
def password_reset_request(
    req: PasswordResetRequest, db: Session = Depends(get_db)
) -> dict[str, str]:
    auth_service.request_password_reset(req.email, db)
    return {"detail": "Se o e-mail existir, enviaremos as instruções."}
