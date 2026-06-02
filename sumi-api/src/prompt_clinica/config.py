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
    ai_provider: str = field(default_factory=lambda: _optional("AI_PROVIDER", "openai"))
    ai_text_model: str = field(default_factory=lambda: _optional("AI_TEXT_MODEL", "gpt-4o-mini"))
    ai_image_model: str = field(default_factory=lambda: _optional("AI_IMAGE_MODEL", "gpt-image-1"))
    images_dir: str = field(default_factory=lambda: _optional("IMAGES_DIR", "static/images"))
    storage_backend: str = field(default_factory=lambda: _optional("STORAGE_BACKEND", "local"))
    railway_bucket_name: str = field(default_factory=lambda: _optional("BUCKET_NAME") or _optional("RAILWAY_BUCKET_NAME"))
    railway_bucket_endpoint_url: str = field(default_factory=lambda: _optional("BUCKET_ENDPOINT_URL") or _optional("RAILWAY_BUCKET_ENDPOINT_URL"))
    railway_bucket_access_key: str = field(default_factory=lambda: _optional("BUCKET_ACCESS_KEY_ID") or _optional("RAILWAY_BUCKET_ACCESS_KEY"))
    railway_bucket_secret_key: str = field(default_factory=lambda: _optional("BUCKET_SECRET_ACCESS_KEY") or _optional("RAILWAY_BUCKET_SECRET_KEY"))
    railway_bucket_region: str = field(default_factory=lambda: _optional("BUCKET_REGION") or _optional("RAILWAY_BUCKET_REGION") or "auto")
    railway_public_url: str = field(default_factory=lambda: _optional("PUBLIC_URL") or _optional("RAILWAY_PUBLIC_URL"))
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
