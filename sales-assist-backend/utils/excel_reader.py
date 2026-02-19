import pandas as pd
from logger import enhanced_logger
from typing import List


def extract_text_from_excel(file_bytes: bytes, filename: str) -> List[str]:
    enhanced_logger.info(f"Reading Excel file {filename}")

    xls = pd.ExcelFile(file_bytes)
    chunks = []

    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        for _, row in df.iterrows():
            text = "; ".join(f"{col}={row[col]}" for col in df.columns if pd.notna(row[col]))
            chunks.append(text)

    enhanced_logger.info(f"Generated {len(chunks)} chunks from Excel")
    return chunks
