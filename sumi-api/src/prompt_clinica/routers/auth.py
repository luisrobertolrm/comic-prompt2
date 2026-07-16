from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from prompt_clinica.database import get_db
from prompt_clinica.schemas.auth import (
    LoginRequest,
    PasswordResetRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from prompt_clinica.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201, response_model=RegisterResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    return auth_service.register(req, db)


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return auth_service.login(req, db)


@router.post("/password-reset/request", status_code=202)
def password_reset_request(
    req: PasswordResetRequest, db: Session = Depends(get_db)
) -> dict[str, str]:
    auth_service.request_password_reset(req.email, db)
    return {"detail": "Se o e-mail existir, enviaremos as instruções."}
