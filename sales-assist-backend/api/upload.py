from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from pathlib import Path
import os
import hashlib

from logger import enhanced_logger
from config.domains import is_valid_domain
from services.ingestion_service import ingest_file
from services.mongo_service import (
    find_file_by_hash,
    insert_file_metadata,
    update_file_status,
)

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    domain: str = Form(...),
    background_tasks: BackgroundTasks = None,
):
    try:
        if not is_valid_domain(domain):
            raise HTTPException(status_code=400, detail="Invalid domain")

        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Empty document")

        max_mb = int(os.getenv("MAX_FILE_SIZE_MB", "25"))
        if len(contents) > max_mb * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large")

        # 1. Duplicate detection (sha256)
        file_hash = hashlib.sha256(contents).hexdigest()
        existing = await find_file_by_hash(file_hash, domain=domain)
        if existing:
            return {
                "file_id": str(existing["_id"]),
                "processing_status": existing.get("processing_status", "uploaded"),
                "domain": existing.get("domain", domain),
            }

        # 2. Save metadata in Mongo
        file_id = await insert_file_metadata(
            filename=file.filename,
            content_type=file.content_type or "",
            domain=domain,
            file_hash=file_hash,
        )

        # 2. Save file to disk
        upload_dir = Path("uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_name = Path(file.filename).name
        file_path = upload_dir / f"{file_id}_{safe_name}"
        with open(file_path, "wb") as f:
            f.write(contents)

        await update_file_status(
            file_id,
            "uploaded",
            extra_fields={"file_path": str(file_path)},
        )

        # 3. Ingest (async background)
        processing_status = "processing"
        if background_tasks is not None:
            background_tasks.add_task(ingest_file, str(file_path), domain, file_id)
            await update_file_status(file_id, "processing")
        else:
            await ingest_file(str(file_path), domain, file_id)
            processing_status = "completed"

        return {
            "file_id": file_id,
            "processing_status": processing_status,
            "domain": domain,
        }

    except HTTPException:
        raise
    except Exception as e:
        enhanced_logger.exception("UPLOAD_FAILED", exc_info=e)
        raise HTTPException(status_code=500, detail=str(e))
