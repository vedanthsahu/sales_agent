from logger import enhanced_logger

def extract_text_from_txt(file_bytes: bytes) -> str:
    """
    Extracts plain text from a TXT file.

    Args:
        file_bytes: The TXT file as bytes.

    Returns:
        str: Extracted plain text.
    """
    enhanced_logger.debug("Extracting text from TXT bytes.")
    try:
        text = file_bytes.decode("utf-8", errors="ignore")
        enhanced_logger.info(f"Successfully extracted {len(text)} characters from TXT.")
        return text
    except Exception as e:
        enhanced_logger.exception("Failed to extract text from TXT.", exc_info=e)
        raise Exception(f"Failed to extract text from TXT: {e}")