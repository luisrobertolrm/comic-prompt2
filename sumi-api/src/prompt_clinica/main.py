import prompt_clinica._paths  # noqa: F401 — models/ no sys.path antes de tudo

import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from prompt_clinica.config import settings
from prompt_clinica.routers import (
    auth,
    character_options,
    characters,
    health,
    image_test,
    panels,
    projects,
    series,
    storage,
    styles,
    voice,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sumi.api")

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

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Erro não tratado em %s %s", request.method, request.url.path)
    detail = f"{type(exc).__name__}: {exc}" if settings.is_development else "Erro interno no servidor."
    response = JSONResponse(status_code=500, content={"detail": detail})
    # ServerErrorMiddleware fica fora do CORSMiddleware — adiciona o header na mão
    # para que a mensagem chegue ao browser em vez de ser bloqueada por CORS.
    origin = request.headers.get("origin")
    if origin in settings.cors_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(series.router)
app.include_router(characters.router)
app.include_router(character_options.router)
app.include_router(panels.router)
app.include_router(storage.router)
app.include_router(voice.router)
app.include_router(image_test.router)
app.include_router(styles.router)

_static_root = Path("static")
_static_root.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_static_root)), name="static")

_spa_dir = Path("static/app")
if _spa_dir.exists():
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str) -> FileResponse:  # noqa: RUF029
        spa_file = _spa_dir / full_path
        if spa_file.is_file():
            return FileResponse(str(spa_file))
        return FileResponse(str(_spa_dir / "index.html"))


if __name__ == "__main__":
    uvicorn.run(
        "prompt_clinica.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_reload,
    )
