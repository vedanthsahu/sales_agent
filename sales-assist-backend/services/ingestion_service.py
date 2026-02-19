from __future__ import annotations

import time
from typing import List

from logger import enhanced_logger
from rag.ingest_pipeline import extract_text_from_file, chunk_text_for_ingestion
from services.embedding_service import embed_texts_async
from services.milvus_service import delete_embeddings_by_file_id, insert_embeddings
from services.mongo_service import (
    count_chunks_for_file,
    delete_chunks_for_file,
    get_file,
    insert_chunks,
    update_file_status,
)


ALLOWED_DOMAINS = {"rpa", "it", "hr", "security"}


def _build_chunk_id(file_id: str, chunk_index: int) -> str:
    return f"{file_id}:{chunk_index}"


async def ingest_file(file_path: str, domain: str, file_id: str) -> None:
    if domain not in ALLOWED_DOMAINS:
        raise ValueError(f"Invalid domain: {domain}")

    # Idempotency: if already completed with chunks, skip.
    file_doc = await get_file(file_id)
    if file_doc and file_doc.get("processing_status") == "completed":
        existing_chunks = await count_chunks_for_file(file_id)
        if existing_chunks > 0:
            enhanced_logger.info(
                "INGESTION_SKIPPED_ALREADY_COMPLETED",
                extra_data={"file_id": file_id, "domain": domain},
            )
            return

    await update_file_status(file_id, "processing")

    try:
        start_time = time.time()
        # Clean up any partial data before re-ingesting
        await delete_chunks_for_file(file_id)
        delete_embeddings_by_file_id(file_id)

        # Extract text
        text = extract_text_from_file(file_path)
        if not text or not text.strip():
            raise ValueError("Extracted empty text from document")

        # Chunk text
        chunks = chunk_text_for_ingestion(text)
        if not chunks:
            raise ValueError("No chunks created from document")

        # Embed chunks
        embed_start = time.time()
        embeddings = await embed_texts_async(chunks)
        embedding_time_ms = (time.time() - embed_start) * 1000.0

        # Insert into Milvus
        milvus_start = time.time()
        ids: List[str] = []
        metadata = []
        for idx in range(len(chunks)):
            chunk_id = _build_chunk_id(file_id, idx)
            ids.append(chunk_id)
            metadata.append(
                {"file_id": file_id, "domain": domain, "chunk_index": idx}
            )

        insert_embeddings(ids, embeddings, metadata, batch_size=128)
        milvus_insert_time_ms = (time.time() - milvus_start) * 1000.0

        # Insert chunk metadata into Mongo
        chunk_docs = []
        for idx, chunk_text in enumerate(chunks):
            chunk_id = ids[idx]
            chunk_docs.append(
                {
                    "chunk_id": chunk_id,
                    "file_id": file_id,
                    "domain": domain,
                    "chunk_index": idx,
                    "text": chunk_text,
                    "embedding_id": chunk_id,
                }
            )

        await insert_chunks(chunk_docs)

        await update_file_status(
            file_id,
            "completed",
            extra_fields={
                "num_chunks": len(chunks),
                "processing_time_ms": int((time.time() - start_time) * 1000.0),
            },
        )

        enhanced_logger.info(
            "INGESTION_COMPLETED",
            extra_data={
                "file_id": file_id,
                "domain": domain,
                "chunks_created": len(chunks),
                "embedding_time_ms": round(embedding_time_ms, 2),
                "milvus_insert_time_ms": round(milvus_insert_time_ms, 2),
            },
        )

    except Exception as exc:
        enhanced_logger.exception(
            "INGESTION_FAILED",
            exc_info=exc,
            extra_data={"file_id": file_id, "domain": domain},
        )
        await update_file_status(
            file_id,
            "failed",
            extra_fields={"error": str(exc)},
        )
        raise
