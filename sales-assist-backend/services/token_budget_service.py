from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from rag.tokenizer import count_tokens


@dataclass(frozen=True)
class TokenBudget:
    max_history_tokens: int
    max_rag_tokens: int
    max_input_tokens: int
    max_output_tokens: int


def load_token_budget() -> TokenBudget:
    return TokenBudget(
        max_history_tokens=int(os.getenv("MAX_HISTORY_TOKENS", "2000")),
        max_rag_tokens=int(os.getenv("MAX_RAG_TOKENS", "1500")),
        max_input_tokens=int(os.getenv("MAX_INPUT_TOKENS", "4000")),
        max_output_tokens=int(os.getenv("GEMINI_MAX_TOKENS", "2048")),
    )


def count_history_tokens(history: List[Dict[str, Any]]) -> int:
    total = 0
    for item in history:
        parts = item.get("parts") or []
        for part in parts:
            total += count_tokens(part.get("text", ""))
    return total


def trim_history(history: List[Dict[str, Any]], max_tokens: int) -> Tuple[List[Dict[str, Any]], int]:
    if max_tokens <= 0:
        return list(history or []), count_history_tokens(history or [])
    trimmed = list(history or [])
    while trimmed and count_history_tokens(trimmed) > max_tokens:
        trimmed.pop(0)
    return trimmed, count_history_tokens(trimmed)


def _count_rag_tokens(records: List[Dict[str, Any]]) -> int:
    return sum(count_tokens(r.get("text", "")) for r in records)


def trim_rag_records(
    records: List[Dict[str, Any]],
    max_tokens: int,
) -> Tuple[List[Dict[str, Any]], int]:
    if max_tokens <= 0:
        return list(records or []), _count_rag_tokens(records or [])
    trimmed: List[Dict[str, Any]] = []
    total = 0
    for rec in records or []:
        text = rec.get("text", "")
        tokens = count_tokens(text)
        if total + tokens > max_tokens:
            break
        trimmed.append(rec)
        total += tokens
    return trimmed, total


def enforce_input_budget(
    system_prompt: str,
    history: List[Dict[str, Any]],
    user_message: str,
    rag_records: List[Dict[str, Any]],
    budget: TokenBudget,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, int]]:
    system_tokens = count_tokens(system_prompt)
    user_tokens = count_tokens(user_message)

    trimmed_history, history_tokens = trim_history(history, budget.max_history_tokens)
    trimmed_rag, rag_tokens = trim_rag_records(rag_records, budget.max_rag_tokens)

    total = system_tokens + history_tokens + user_tokens + rag_tokens

    if budget.max_input_tokens > 0 and total > budget.max_input_tokens:
        # Prefer trimming history first (oldest).
        while trimmed_history and total > budget.max_input_tokens:
            trimmed_history = trimmed_history[1:]
            history_tokens = count_history_tokens(trimmed_history)
            total = system_tokens + history_tokens + user_tokens + rag_tokens

        # If still too large, trim RAG context.
        if total > budget.max_input_tokens:
            remaining_for_rag = max(budget.max_input_tokens - (system_tokens + history_tokens + user_tokens), 0)
            trimmed_rag, rag_tokens = trim_rag_records(trimmed_rag, remaining_for_rag)
            total = system_tokens + history_tokens + user_tokens + rag_tokens

    usage = {
        "system_tokens": system_tokens,
        "history_tokens": history_tokens,
        "user_tokens": user_tokens,
        "rag_tokens": rag_tokens,
        "total_tokens": total,
    }

    return trimmed_history, trimmed_rag, usage
