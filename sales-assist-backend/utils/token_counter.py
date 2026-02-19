# utils/token_counter.py
import tiktoken

def count_tokens(text: str, model_name: str = "gpt-4o-mini") -> int:
    """
    Count tokens for a given text and model.
    Falls back to cl100k_base if model not recognized.
    """
    if not text:
        return 0
    try:
        enc = tiktoken.encoding_for_model(model_name)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))

