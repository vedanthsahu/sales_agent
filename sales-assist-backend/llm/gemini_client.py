import os
from typing import Dict, List, Optional

import google.generativeai as genai


# Initialize Gemini once
_api_key = os.getenv("GEMINI_API_KEY")
_model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

if not _api_key:
    raise RuntimeError("GEMINI_API_KEY not set in environment")

genai.configure(api_key=_api_key)


def get_model_name() -> str:
    return _model_name


def chat_completion(
    system_prompt: str,
    history: List[Dict],
    user_message: str,
    temperature: Optional[float] = None,
    max_output_tokens: Optional[int] = None,
) -> str:
    """
    Simple, synchronous Gemini chat completion.
    Returns plain text.
    """

    generation_config = {}
    if temperature is not None:
        generation_config["temperature"] = float(temperature)
    if max_output_tokens is not None:
        generation_config["max_output_tokens"] = int(max_output_tokens)

    model_kwargs = {
        "model_name": _model_name,
        "system_instruction": system_prompt,
    }
    if generation_config:
        model_kwargs["generation_config"] = generation_config

    model = genai.GenerativeModel(**model_kwargs)

    chat = model.start_chat(history=history)

    response = chat.send_message(user_message)

    if not response or not response.text:
        raise RuntimeError("Empty response from Gemini")

    return response.text
