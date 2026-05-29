import prompt_clinica._paths  # noqa: F401 — models/ no sys.path antes de tudo

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from prompt_clinica.config import settings
from prompt_clinica.routers import auth, health

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


if __name__ == "__main__":
    uvicorn.run(
        "prompt_clinica.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_reload,
    )
