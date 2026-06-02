# Importe aqui todos os modelos para que o Alembic os detecte via Base.metadata.
from character import Character
from panel import Panel
from project import Project
from project_character import ProjectCharacter
from temp_portrait import TempPortrait
from user import PasswordResetToken, User, UserOAuth, UserSession
from youtube_metadata import VideoMetadata

__all__ = ["User", "UserOAuth", "PasswordResetToken", "UserSession", "Project", "Character", "ProjectCharacter", "VideoMetadata", "TempPortrait"]
