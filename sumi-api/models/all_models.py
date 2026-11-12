# Importe aqui todos os modelos para que o Alembic os detecte via Base.metadata.
from ai_image_config import AIImageConfig
from ai_text_config import AITextConfig
from ai_transcription_config import AITranscriptionConfig
from ai_video_config import AIVideoConfig
from ai_voice_config import AIVoiceConfig
from character import Character
from narration_voice import NarrationVoice
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

__all__ = ["AIImageConfig", "AITextConfig", "AITranscriptionConfig", "AIVideoConfig", "AIVoiceConfig", "Character", "Group", "NarrationVoice", "PasswordResetToken", "Project", "ProjectCharacter", "ProjectScenario", "RecomendacaoNegativa", "RecomendacaoPositiva", "RecomendacaoUsuario", "Scenario", "Series", "SeriesProject", "TempPortrait", "User", "UserOAuth", "UserSession", "UserSettings", "VideoMetadata", "VisualStyle"]
