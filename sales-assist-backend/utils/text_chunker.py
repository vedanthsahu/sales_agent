from typing import List, Dict
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from logger import enhanced_logger


def chunk_text_by_newlines(
    text: str,
    chunk_size: int = None,
    overlap: int = None,
    preserve_structure: bool = True
) -> List[str]:
    if chunk_size is None:
        chunk_size = config.CHUNK_SIZE
    if overlap is None:
        overlap = config.CHUNK_OVERLAP

    enhanced_logger.debug(
        f"Chunking text length={len(text)} chunk_size={chunk_size} overlap={overlap}"
    )

    if preserve_structure:
        chunks = _chunk_with_structure(text, chunk_size, overlap)
    else:
        chunks = _chunk_simple(text, chunk_size, overlap)

    enhanced_logger.info(f"Chunked into {len(chunks)} chunks")
    return chunks


def _chunk_simple(text: str, chunk_size: int, overlap: int) -> List[str]:
    processed = _preprocess_text(text)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=len,
        separators=["\n\n\n", "\n\n", "\n", ". ", " ", ""]
    )
    return splitter.split_text(processed)


def _chunk_with_structure(text: str, chunk_size: int, overlap: int) -> List[str]:
    processed_text, table_info = _extract_and_mark_tables(text)
    sections = _split_by_headers(processed_text)

    all_chunks = []
    for section in sections:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            length_function=len,
            separators=["\n\n\n", "\n\n", "\n", ". ", " ", ""]
        )
        all_chunks.extend(splitter.split_text(section))

    return _clean_table_markers(all_chunks, table_info)


def _preprocess_text(text: str) -> str:
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\t', ' ', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()
