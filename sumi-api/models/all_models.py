# Importe aqui todos os modelos para que o Alembic os detecte via Base.metadata.
from character import Character
from panel import Panel
from project import Project
from project_character import ProjectCharacter
from user import PasswordResetToken, User, UserOAuth, UserSession

__all__ = ["User", "UserOAuth", "PasswordResetToken", "UserSession", "Project", "Character", "ProjectCharacter"]
