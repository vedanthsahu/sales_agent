from __future__ import annotations

from typing import Optional


def _get_embedding_tokenizer():
    """
    Try to fetch the embedding tokenizer from the embedding service.
    Returns None if unavailable.
    """
    try:
        from services.embedding_service import get_embedding_tokenizer
    except Exception:
        return None

    try:
        return get_embedding_tokenizer()
    except Exception:
        return None


def count_tokens(text: str) -> int:
    """
    Count tokens using the embedding tokenizer when available.
    Fallback: whitespace word split.
    """
    if not text:
        return 0

    tokenizer = _get_embedding_tokenizer()
    if tokenizer is not None:
        try:
            # Transformers-style tokenizers support encode.
            return len(tokenizer.encode(text, add_special_tokens=False))
        except Exception:
            pass

    # Fallback: naive whitespace split
    return len(text.split())
