import fitz
from logger import enhanced_logger


def extract_text_from_pdf(file_bytes: bytes) -> str:
    enhanced_logger.debug("Extracting text from PDF")

    text = []
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            page_text = page.get_text()
            if page_text:
                text.append(page_text)

    result = "\n".join(text)
    enhanced_logger.info(f"Extracted {len(result)} characters from PDF")
    return result
