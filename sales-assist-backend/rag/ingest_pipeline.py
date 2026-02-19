from __future__ import annotations

import os
from pathlib import Path
from typing import List

from rag.chunker import chunk_text
from utils.pdf_reader import extract_text_from_pdf
from utils.doc_reader import extract_text_from_docx
from utils.txt_reader import extract_text_from_txt


def extract_text_from_file(file_path: str) -> str:
    """
    Extract raw text from a file path using the appropriate reader.
    """
    ext = Path(file_path).suffix.lower()
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    if ext == ".pdf":
        return extract_text_from_pdf(file_bytes)
    if ext in (".doc", ".docx"):
        return extract_text_from_docx(file_bytes)
    if ext == ".txt":
        return extract_text_from_txt(file_bytes)

    raise ValueError(f"Unsupported file type: {ext}")


def chunk_text_for_ingestion(text: str) -> List[str]:
    """
    Chunk text using configured token sizes.
    """
    chunk_size = int(os.getenv("CHUNK_SIZE", "500"))
    overlap = int(os.getenv("CHUNK_OVERLAP", "50"))
    return chunk_text(text, chunk_size_tokens=chunk_size, overlap_tokens=overlap)
