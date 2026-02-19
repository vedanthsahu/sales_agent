from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from agents.domain_prompts import DOMAIN_PROMPTS
from llm.gemini_client import chat_completion


def get_system_prompt(domain: str) -> str:
    base_system_prompt = os.getenv(
        "SYSTEM_PROMPT",
        "You are a sales assistant AI. Answer clearly and only using the provided context when available.",
    )
    domain_prompt = DOMAIN_PROMPTS.get(domain, "")

    system_prompt = base_system_prompt
    if domain_prompt:
        system_prompt = f"{base_system_prompt}\n\nDomain Focus:\n{domain_prompt}"

    output_contract = (
        "Return ONLY valid JSON with this exact shape:\n"
        "{\n"
        '  "answer": "<plain text answer>",\n'
        '  "follow_up_questions": ["q1", "q2"],\n'
        '  "confidence_score": 0.0\n'
        "}\n"
        "Rules:\n"
        "- follow_up_questions must be exactly 2 short strings.\n"
        "- confidence_score must be a number between 0 and 1.\n"
        "- Do not include markdown or extra keys.\n"
    )

    return f"{system_prompt}\n\n{output_contract}"


def build_user_message(user_message: str, rag_context: Optional[str]) -> str:
    if rag_context:
        return (
            "Context:\n"
            f"{rag_context}\n\n"
            "Question:\n"
            f"{user_message}"
        )
    return user_message


def _coerce_followups(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    result: List[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
    return result[:2]


def _coerce_confidence(value: Any) -> float:
    try:
        score = float(value)
    except Exception:
        return 0.0
    if score < 0.0:
        return 0.0
    if score > 1.0:
        return 1.0
    return score


def _parse_structured_response(raw_text: str) -> Dict[str, Any]:
    if not raw_text:
        return {"answer": "", "follow_up_questions": [], "confidence_score": 0.0}

    payload: Optional[Dict[str, Any]] = None
    try:
        payload = json.loads(raw_text)
    except Exception:
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                payload = json.loads(raw_text[start : end + 1])
            except Exception:
                payload = None

    if not isinstance(payload, dict):
        return {
            "answer": raw_text.strip(),
            "follow_up_questions": [],
            "confidence_score": 0.0,
        }

    answer = payload.get("answer", "")
    followups = _coerce_followups(payload.get("follow_up_questions", []))
    confidence = _coerce_confidence(payload.get("confidence_score", 0.0))

    return {
        "answer": str(answer).strip(),
        "follow_up_questions": followups,
        "confidence_score": confidence,
    }


async def generate_domain_response(
    domain: str,
    user_message: str,
    rag_context: Optional[str] = None,
    history: Optional[List[Dict[str, Any]]] = None,
    max_output_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
) -> Tuple[Dict[str, Any], str]:
    """
    Build a domain-aware prompt, request structured JSON, and parse safely.
    Returns (parsed_response, raw_text).
    """
    system_prompt = get_system_prompt(domain)
    final_user_message = build_user_message(user_message, rag_context)

    raw_text = chat_completion(
        system_prompt=system_prompt,
        history=history or [],
        user_message=final_user_message,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )

    parsed = _parse_structured_response(raw_text)
    return parsed, raw_text
