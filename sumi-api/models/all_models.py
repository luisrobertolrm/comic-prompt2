# Importe aqui todos os modelos para que o Alembic os detecte via Base.metadata.
from user import PasswordResetToken, User, UserOAuth, UserSession

__all__ = ["User", "UserOAuth", "PasswordResetToken", "UserSession"]
