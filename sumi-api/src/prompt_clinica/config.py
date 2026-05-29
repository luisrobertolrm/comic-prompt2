import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    value = os.getenv(key, "")
    if not value:
        raise ValueError(f"Variável de ambiente obrigatória não definida: {key}")
    return value


def _optional(key: str, default: str = "") -> str:
    return os.getenv(key, default)


@dataclass(frozen=True)
class Settings:
    database_url: str = field(default_factory=lambda: _require("DATABASE_URL"))
    google_api_key: str = field(default_factory=lambda: _optional("GOOGLE_API_KEY"))
    openai_api_key: str = field(default_factory=lambda: _optional("OPENAI_API_KEY"))
    app_env: str = field(default_factory=lambda: _optional("APP_ENV", "development"))
    app_host: str = field(default_factory=lambda: _optional("APP_HOST", "0.0.0.0"))
    app_port: int = field(
        default_factory=lambda: int(_optional("APP_PORT", "8000"))
    )
    app_reload: bool = field(
        default_factory=lambda: _optional("APP_RELOAD", "true").lower() == "true"
    )
    jwt_secret_key: str = field(
        default_factory=lambda: _require("JWT_SECRET_KEY")
    )
    jwt_expire_minutes: int = field(
        default_factory=lambda: int(_optional("JWT_EXPIRE_MINUTES", "60"))
    )
    cors_origins: list[str] = field(
        default_factory=lambda: [
            o.strip() for o in _optional("CORS_ORIGINS", "http://localhost:4200").split(",")
        ]
    )

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


settings = Settings()
