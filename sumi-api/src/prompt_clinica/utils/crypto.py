import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from prompt_clinica.config import settings


def _fernet() -> Fernet:
    # Derivada do JWT_SECRET_KEY: trocar o segredo invalida as chaves salvas.
    digest = hashlib.sha256(settings.jwt_secret_key.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode() if value else ""


def decrypt(token: str) -> str:
    """Vazio se `token` estiver vazio ou não puder ser lido com o segredo atual."""
    if not token:
        return ""
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken:
        return ""
