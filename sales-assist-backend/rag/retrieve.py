import os
from typing import Any, Dict, List, Optional

from services.embedding_service import embed_query_async
from services.milvus_service import search_embeddings
from services.mongo_service import get_chunks_by_ids


async def retrieve_chunks(
    query: str,
    file_ids: List[str],
    domain: Optional[str] = None,
    top_k: int = None,
) -> List[str]:
    """
    Retrieve relevant text chunks from Milvus for given file_ids.
    """
    top_k = top_k or int(os.getenv("MILVUS_TOP_K", 5))

    query_embedding = await embed_query_async(query)
    if not query_embedding:
        return []

    hits = search_embeddings(
        query_embedding=query_embedding,
        top_k=top_k,
        file_ids=file_ids,
        domain=domain,
    )

    chunk_ids: List[str] = []
    for hit in hits:
        chunk_id = None
        if hasattr(hit, "entity") and hit.entity is not None:
            chunk_id = hit.entity.get("id")
        if not chunk_id:
            chunk_id = getattr(hit, "id", None)
        if chunk_id:
            chunk_ids.append(chunk_id)

    if not chunk_ids:
        return []

    chunk_map = await get_chunks_by_ids(chunk_ids)
    return [chunk_map[cid]["text"] for cid in chunk_ids if cid in chunk_map]


async def retrieve_chunks_with_scores(
    query: str,
    file_ids: List[str],
    domain: Optional[str] = None,
    top_k: int = None,
):
    """
    Retrieve relevant text chunks and similarity scores.
    """
    top_k = top_k or int(os.getenv("MILVUS_TOP_K", 5))

    query_embedding = await embed_query_async(query)
    if not query_embedding:
        return [], []

    hits = search_embeddings(
        query_embedding=query_embedding,
        top_k=top_k,
        file_ids=file_ids,
        domain=domain,
    )

    chunk_pairs: List[tuple[str, float]] = []
    for hit in hits:
        chunk_id = None
        if hasattr(hit, "entity") and hit.entity is not None:
            chunk_id = hit.entity.get("id")
        if not chunk_id:
            chunk_id = getattr(hit, "id", None)
        score = getattr(hit, "score", None)
        if score is None:
            score = getattr(hit, "distance", None)
        if chunk_id:
            chunk_pairs.append((chunk_id, float(score) if score is not None else 0.0))

    if not chunk_pairs:
        return [], []

    chunk_ids = [cid for cid, _ in chunk_pairs]
    chunk_map = await get_chunks_by_ids(chunk_ids)
    chunks: List[str] = []
    scores: List[float] = []
    for cid, score in chunk_pairs:
        if cid in chunk_map:
            chunks.append(chunk_map[cid]["text"])
            scores.append(score)

    return chunks, scores


async def retrieve_chunk_records(
    query: str,
    file_ids: List[str],
    domain: Optional[str] = None,
    top_k: int = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve chunks with metadata and scores for RAG + source attribution.
    """
    top_k = top_k or int(os.getenv("MILVUS_TOP_K", 5))

    query_embedding = await embed_query_async(query)
    if not query_embedding:
        return []

    hits = search_embeddings(
        query_embedding=query_embedding,
        top_k=top_k,
        file_ids=file_ids,
        domain=domain,
    )

    records: List[Dict[str, Any]] = []
    for hit in hits:
        chunk_id = None
        if hasattr(hit, "entity") and hit.entity is not None:
            chunk_id = hit.entity.get("id")
        if not chunk_id:
            chunk_id = getattr(hit, "id", None)

        score = getattr(hit, "score", None)
        if score is None:
            score = getattr(hit, "distance", None)

        file_id = None
        domain_value = None
        chunk_index = None
        if hasattr(hit, "entity") and hit.entity is not None:
            file_id = hit.entity.get("file_id")
            domain_value = hit.entity.get("domain")
            chunk_index = hit.entity.get("chunk_index")

        if chunk_id:
            records.append(
                {
                    "chunk_id": str(chunk_id),
                    "file_id": str(file_id) if file_id is not None else None,
                    "domain": str(domain_value) if domain_value is not None else None,
                    "chunk_index": int(chunk_index) if chunk_index is not None else None,
                    "score": float(score) if score is not None else 0.0,
                }
            )

    if not records:
        return []

    chunk_ids = [r["chunk_id"] for r in records]
    chunk_map = await get_chunks_by_ids(chunk_ids)

    hydrated: List[Dict[str, Any]] = []
    for rec in records:
        chunk = chunk_map.get(rec["chunk_id"])
        if not chunk:
            continue
        rec["text"] = chunk.get("text", "")
        hydrated.append(rec)

    return hydrated
