from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from prompt_clinica.storage import get_storage

router = APIRouter(tags=["storage"])


@router.get("/storage/{key:path}")
def serve_file(key: str) -> Response:
    data = get_storage().read(key)
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo não encontrado.")
    suffix = key.rsplit(".", 1)[-1].lower()
    media_type = "image/png" if suffix == "png" else "image/jpeg" if suffix in ("jpg", "jpeg") else "application/octet-stream"
    return Response(content=data, media_type=media_type)
