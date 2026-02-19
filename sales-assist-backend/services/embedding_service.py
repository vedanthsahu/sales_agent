from __future__ import annotations

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

from sentence_transformers import SentenceTransformer


_model: Optional[SentenceTransformer] = None
_executor: Optional[ThreadPoolExecutor] = None


def _load_model() -> SentenceTransformer:
    model_name = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2",
    )
    return SentenceTransformer(model_name)


def get_embedding_model() -> SentenceTransformer:
    """
    Singleton model load to avoid per-request initialization.
    """
    global _model
    if _model is None:
        _model = _load_model()
    return _model


def _get_executor() -> ThreadPoolExecutor:
    global _executor
    if _executor is None:
        workers = int(os.getenv("EMBEDDING_WORKERS", "2"))
        _executor = ThreadPoolExecutor(max_workers=max(1, workers))
    return _executor


def get_embedding_tokenizer():
    """
    Return the tokenizer attached to the embedding model when available.
    """
    model = get_embedding_model()
    return getattr(model, "tokenizer", None)


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Batch embed a list of texts.
    """
    if not texts:
        return []

    model = get_embedding_model()
    batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    return embeddings.tolist()


async def embed_texts_async(texts: List[str]) -> List[List[float]]:
    """
    Non-blocking embedding call for async contexts.
    """
    if not texts:
        return []
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_get_executor(), embed_texts, texts)


async def embed_query_async(query: str) -> List[float]:
    """
    Convenience wrapper for a single query embedding.
    """
    if not query:
        return []
    embeddings = await embed_texts_async([query])
    if not embeddings:
        return []
    return embeddings[0]


# Backwards compatibility for existing retrieval code
def get_retrieval_model() -> SentenceTransformer:
    return get_embedding_model()
