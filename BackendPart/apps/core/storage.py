from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from utils.config import DOC_STORAGE_DIR


async def save_document_file(upload: UploadFile) -> tuple[str, str, int, str]:
    base = Path(DOC_STORAGE_DIR)
    base.mkdir(parents=True, exist_ok=True)

    orig_name = upload.filename or "document"
    ext = Path(orig_name).suffix
    key = f"{uuid4()}{ext}"
    dst = base / key

    size = 0
    with dst.open("wb") as f:
        async for chunk in _iter_file(upload):
            f.write(chunk)
            size += len(chunk)

    content_type = upload.content_type or "application/octet-stream"
    return orig_name, key, size, content_type


async def _iter_file(upload: UploadFile, chunk_size: int = 1024 * 1024):
    while True:
        chunk = await upload.read(chunk_size)
        if not chunk:
            break
        yield chunk
