from pydantic import BaseModel, EmailStr, field_validator, model_validator


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    confirm: str
    terms_accepted: bool

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Como devemos te chamar?")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Mínimo de 6 caracteres.")
        return v

    @field_validator("terms_accepted")
    @classmethod
    def terms_must_be_true(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Aceite os termos para continuar.")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterRequest":
        if self.password != self.confirm:
            raise ValueError("As senhas não conferem.")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember: bool = False


class OAuthGuestRequest(BaseModel):
    pass


class PasswordResetRequest(BaseModel):
    email: EmailStr


class UserOut(BaseModel):
    id: str
    name: str
    email: str | None
    plan: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
