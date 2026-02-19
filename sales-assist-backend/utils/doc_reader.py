import docx
import tempfile
import os
from logger import enhanced_logger


def extract_text_from_docx(file_bytes: bytes) -> str:
    enhanced_logger.debug("Extracting text from DOCX")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(file_bytes)
        path = tmp.name

    doc = docx.Document(path)
    os.remove(path)

    text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    enhanced_logger.info(f"Extracted {len(text)} characters from DOCX")
    return text
