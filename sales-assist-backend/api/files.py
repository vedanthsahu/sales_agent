from fastapi import APIRouter, HTTPException

from config.domains import is_ingest_domain
from services.mongo_service import get_file, list_files

router = APIRouter()


@router.get("/files")
async def get_files(domain: str | None = None):
    if domain and not is_ingest_domain(domain):
        raise HTTPException(status_code=400, detail="Invalid domain")
    return await list_files(domain=domain)


@router.get("/files/{file_id}/status")
async def get_file_status(file_id: str):
    doc = await get_file(file_id)
    if not doc:
        raise HTTPException(status_code=404, detail="File not found")

    processing_status = doc.get("processing_status", "uploaded")
    embedding_status = doc.get("embedding_status")
    if not embedding_status:
        if processing_status == "completed":
            embedding_status = "completed"
        elif processing_status == "failed":
            embedding_status = "failed"
        elif processing_status == "processing":
            embedding_status = "processing"
        else:
            embedding_status = "pending"

    return {
        "processing_status": processing_status,
        "embedding_status": embedding_status,
    }
