# Importe aqui todos os modelos para que o Alembic os detecte via Base.metadata.
from character import Character
from narration_voice import NarrationVoice
from panel import Panel
from project import Project
from project_character import ProjectCharacter
from project_scenario import ProjectScenario
from recomendacao import RecomendacaoNegativa, RecomendacaoPositiva, RecomendacaoUsuario
from scenario import Scenario
from series import Series
from series_project import SeriesProject
from temp_portrait import TempPortrait
from user import Group, PasswordResetToken, User, UserOAuth, UserSession
from user_settings import UserSettings
from visual_style import VisualStyle
from youtube_metadata import VideoMetadata

__all__ = ["Group", "User", "UserOAuth", "PasswordResetToken", "UserSession", "UserSettings", "Project", "Character", "ProjectCharacter", "Scenario", "ProjectScenario", "Series", "SeriesProject", "VideoMetadata", "TempPortrait", "NarrationVoice", "VisualStyle", "RecomendacaoPositiva", "RecomendacaoNegativa", "RecomendacaoUsuario"]
