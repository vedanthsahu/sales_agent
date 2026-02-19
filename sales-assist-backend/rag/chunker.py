from __future__ import annotations

import re
from typing import List, Tuple

from rag.tokenizer import count_tokens


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")


def _split_into_sentences(text: str) -> List[str]:
    if not text:
        return []
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    normalized = normalized.strip()
    if not normalized:
        return []
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(normalized) if s.strip()]


def _split_long_sentence(sentence: str, chunk_size_tokens: int) -> List[str]:
    """
    Split a long sentence into smaller parts by words to respect chunk size.
    """
    words = sentence.split()
    if not words:
        return []

    parts: List[str] = []
    current: List[str] = []
    current_tokens = 0

    for word in words:
        tentative = " ".join(current + [word])
        tentative_tokens = count_tokens(tentative)
        if tentative_tokens <= chunk_size_tokens:
            current.append(word)
            current_tokens = tentative_tokens
            continue

        if current:
            parts.append(" ".join(current))
        # Start new part with the current word
        current = [word]
        current_tokens = count_tokens(word)

        # If a single word is somehow longer than chunk size, force split
        if current_tokens > chunk_size_tokens:
            parts.append(word)
            current = []
            current_tokens = 0

    if current:
        parts.append(" ".join(current))

    return parts


def _build_overlap_segments(
    segments: List[Tuple[str, int]],
    overlap_tokens: int,
) -> Tuple[List[Tuple[str, int]], int]:
    if overlap_tokens <= 0 or not segments:
        return [], 0

    overlap: List[Tuple[str, int]] = []
    total = 0
    for seg, tok in reversed(segments):
        if total >= overlap_tokens:
            break
        overlap.append((seg, tok))
        total += tok

    overlap.reverse()
    return overlap, total


def chunk_text(
    text: str,
    chunk_size_tokens: int = 500,
    overlap_tokens: int = 50,
) -> List[str]:
    """
    Chunk text by sentence boundaries when possible, without exceeding chunk size.
    """
    if not text or not text.strip():
        return []

    sentences = _split_into_sentences(text)
    segments: List[Tuple[str, int]] = []

    for sentence in sentences:
        tokens = count_tokens(sentence)
        if tokens <= chunk_size_tokens:
            segments.append((sentence, tokens))
        else:
            for part in _split_long_sentence(sentence, chunk_size_tokens):
                part_tokens = count_tokens(part)
                segments.append((part, part_tokens))

    chunks: List[str] = []
    current_segments: List[Tuple[str, int]] = []

    for segment, seg_tokens in segments:
        if not current_segments:
            current_segments.append((segment, seg_tokens))
            continue

        candidate_text = " ".join([s for s, _ in current_segments] + [segment])
        if count_tokens(candidate_text) <= chunk_size_tokens:
            current_segments.append((segment, seg_tokens))
            continue

        # Flush current chunk
        chunks.append(" ".join(s for s, _ in current_segments).strip())

        # Build overlap for next chunk
        current_segments, _ = _build_overlap_segments(
            current_segments,
            overlap_tokens,
        )

        # Drop overlap until the new segment fits
        while current_segments:
            candidate_text = " ".join([s for s, _ in current_segments] + [segment])
            if count_tokens(candidate_text) <= chunk_size_tokens:
                break
            current_segments.pop(0)

        current_segments.append((segment, seg_tokens))

    if current_segments:
        chunks.append(" ".join(s for s, _ in current_segments).strip())

    return chunks
