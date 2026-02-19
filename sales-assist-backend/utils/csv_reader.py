import pandas as pd
from logger import enhanced_logger
from typing import List
import io
import csv

def extract_text_from_csv(file_bytes: bytes, filename: str, rows_per_chunk: int = 1, encoding: str = "utf-8") -> List[str]:
    """
    Reads a CSV file and converts it into header-augmented row-based text chunks.

    Args:
        file_bytes (bytes): Raw bytes of the CSV file.
        filename (str): Name of the file (for logging).
        rows_per_chunk (int): Number of rows per chunk (default 1).
        encoding (str): File encoding (default "utf-8").

    Returns:
        List[str]: List of text chunks, each containing headers + row(s).
    """
    try:
        enhanced_logger.info(f"Reading CSV file: {filename}")

        # Convert bytes to a buffer for pandas
        csv_buffer = io.BytesIO(file_bytes)

        # Attempt to detect delimiter if unsure
        sample = csv_buffer.read(1024).decode(encoding)
        csv_buffer.seek(0)  # reset buffer
        dialect = csv.Sniffer().sniff(sample)
        delimiter = dialect.delimiter

        # Read CSV into DataFrame
        df = pd.read_csv(csv_buffer, delimiter=delimiter, encoding=encoding)

        if df.empty:
            enhanced_logger.info(f"CSV file '{filename}' is empty.")
            return []

        # Ensure headers are strings
        df.columns = df.columns.map(str)

        all_chunks = []

        # Process in row chunks
        for start_idx in range(0, len(df), rows_per_chunk):
            end_idx = min(start_idx + rows_per_chunk, len(df))
            chunk_rows = df.iloc[start_idx:end_idx]

            headers = " | ".join(chunk_rows.columns)
            row_texts = []
            for _, row in chunk_rows.iterrows():
                row_str = " | ".join([str(cell) if pd.notna(cell) else "" for cell in row])
                row_texts.append(row_str)

            chunk_text = f"Headers: {headers} | Rows: " + " ; ".join(row_texts)
            chunk_text += f" [Rows: {start_idx + 1}-{end_idx}]"

            all_chunks.append(chunk_text)

        enhanced_logger.info(f"CSV file '{filename}' processed into {len(all_chunks)} chunks.")
        return all_chunks

    except Exception as e:
        enhanced_logger.exception(f"Failed to process CSV file: {filename}", exc_info=e)
        raise ValueError(f"Error processing CSV file: {filename}") from e