"""Adiciona models/ ao sys.path em runtime (espelhando o extraPaths do pyright)."""
import sys
from pathlib import Path

_models_dir = Path(__file__).resolve().parents[2] / "models"
if str(_models_dir) not in sys.path:
    sys.path.insert(0, str(_models_dir))
