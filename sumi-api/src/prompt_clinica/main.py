import prompt_clinica._paths  # noqa: F401 — models/ no sys.path antes de tudo

from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from prompt_clinica.config import settings
from prompt_clinica.routers import auth, characters, health, panels, projects

app = FastAPI(
    title="Sumi API",
    version="0.1.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(characters.router)
app.include_router(panels.router)

_static_root = Path(settings.images_dir).parent
_static_root.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_static_root)), name="static")


if __name__ == "__main__":
    uvicorn.run(
        "prompt_clinica.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_reload,
    )
