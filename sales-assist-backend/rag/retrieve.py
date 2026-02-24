import math
import os
import time
import uuid
from typing import Any, Dict, List, Optional

from config.domains import BASE_DOMAINS, is_general_domain
from logger import enhanced_logger
from services.embedding_service import embed_query_async
from services.milvus_service import get_general_collection_name, search_embeddings
from services.mongo_service import get_chunks_by_ids


def _extract_chunk_id(hit: Any) -> Optional[str]:
    if hasattr(hit, "entity") and hit.entity is not None:
        chunk_id = hit.entity.get("id")
        if chunk_id:
            return str(chunk_id)
    chunk_id = getattr(hit, "id", None)
    return str(chunk_id) if chunk_id else None


def _extract_score(hit: Any) -> float:
    score = getattr(hit, "score", None)
    if score is None:
        score = getattr(hit, "distance", None)
    return float(score) if score is not None else 0.0


def _extract_entity_value(hit: Any, key: str):
    if hasattr(hit, "entity") and hit.entity is not None:
        return hit.entity.get(key)
    return None


def _debug_enabled() -> bool:
    flag = os.getenv("RAG_DEBUG", "")
    return str(flag).lower() in {"1", "true", "yes", "on"}


def _log_retrieval_debug(
    query_id: str,
    domain: Optional[str],
    top_k: int,
    hits: List[Any],
    latency_ms: float,
):
    if not _debug_enabled():
        return
    chunk_ids: List[str] = []
    scores: List[float] = []
    for hit in hits:
        cid = _extract_chunk_id(hit)
        if cid:
            chunk_ids.append(cid)
        scores.append(_extract_score(hit))
    enhanced_logger.info(
        "RAG_DEBUG",
        extra_data={
            "query_embedding_id": query_id,
            "domain": domain,
            "top_k": top_k,
            "retrieved_doc_ids": chunk_ids,
            "similarity_scores": scores,
            "latency_ms": round(latency_ms, 2),
        },
    )


def _search_hits(
    query_embedding: List[float],
    top_k: int,
    file_ids: List[str],
    domain: Optional[str],
) -> List[Any]:
    if is_general_domain(domain):
        per_domain_k = int(os.getenv("GENERAL_TOP_K_PER_DOMAIN", "0") or 0)
        if per_domain_k <= 0:
            per_domain_k = max(1, math.ceil(top_k / max(len(BASE_DOMAINS), 1)))
        hits: List[Any] = []
        collection_name = get_general_collection_name()
        for base_domain in sorted(BASE_DOMAINS):
            hits.extend(
                search_embeddings(
                    query_embedding=query_embedding,
                    top_k=per_domain_k,
                    file_ids=[],
                    domain=base_domain,
                    collection_name=collection_name,
                )
            )
        hits.sort(key=_extract_score, reverse=True)
        return hits[:top_k]

    return search_embeddings(
        query_embedding=query_embedding,
        top_k=top_k,
        file_ids=file_ids,
        domain=domain,
    )


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

    search_start = time.time()
    hits = _search_hits(
        query_embedding=query_embedding,
        top_k=top_k,
        file_ids=file_ids,
        domain=domain,
    )
    _log_retrieval_debug(
        query_id=uuid.uuid4().hex,
        domain=domain,
        top_k=top_k,
        hits=hits,
        latency_ms=(time.time() - search_start) * 1000.0,
    )

    chunk_ids: List[str] = []
    for hit in hits:
        chunk_id = _extract_chunk_id(hit)
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

    search_start = time.time()
    hits = _search_hits(
        query_embedding=query_embedding,
        top_k=top_k,
        file_ids=file_ids,
        domain=domain,
    )
    _log_retrieval_debug(
        query_id=uuid.uuid4().hex,
        domain=domain,
        top_k=top_k,
        hits=hits,
        latency_ms=(time.time() - search_start) * 1000.0,
    )

    chunk_pairs: List[tuple[str, float]] = []
    for hit in hits:
        chunk_id = _extract_chunk_id(hit)
        score = _extract_score(hit)
        if chunk_id:
            chunk_pairs.append((chunk_id, score))

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

    search_start = time.time()
    hits = _search_hits(
        query_embedding=query_embedding,
        top_k=top_k,
        file_ids=file_ids,
        domain=domain,
    )
    _log_retrieval_debug(
        query_id=uuid.uuid4().hex,
        domain=domain,
        top_k=top_k,
        hits=hits,
        latency_ms=(time.time() - search_start) * 1000.0,
    )

    records: List[Dict[str, Any]] = []
    for hit in hits:
        chunk_id = _extract_chunk_id(hit)
        score = _extract_score(hit)
        file_id = _extract_entity_value(hit, "file_id")
        domain_value = _extract_entity_value(hit, "domain")
        chunk_index = _extract_entity_value(hit, "chunk_index")

        if chunk_id:
            records.append(
                {
                    "chunk_id": str(chunk_id),
                    "file_id": str(file_id) if file_id is not None else None,
                    "domain": str(domain_value) if domain_value is not None else None,
                    "chunk_index": int(chunk_index) if chunk_index is not None else None,
                    "score": score,
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
