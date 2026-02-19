from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import time
import os

from agents.domain_router import generate_domain_response, get_system_prompt
from config.domains import is_valid_domain
from rag.retrieve import retrieve_chunk_records
from rag.tokenizer import count_tokens
from services.token_budget_service import enforce_input_budget, load_token_budget
from logger import enhanced_logger
from llm.gemini_client import get_model_name

router = APIRouter()


class ChatRequest(BaseModel):
    domain: str
    message: str
    file_ids: Optional[List[str]] = Field(default_factory=list)
    history: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    follow_up_questions: List[str]
    sources: List[Dict[str, Any]]
    confidence_score: float
    latency_ms: float


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    POC chat endpoint.
    - No auth
    - No tenants
    - No RBAC
    - UI-selected files only
    """

    start_time = time.time()
    latency_rag = 0.0
    latency_llm = 0.0
    rag_used = False
    chunks_used = 0
    rag_avg_score = 0.0
    tokens_input = 0
    tokens_output = 0
    model_name = get_model_name()
    first_token_latency = 0.0
    fallback_used = False

    try:
        if not is_valid_domain(request.domain):
            raise HTTPException(status_code=400, detail="Invalid domain")

        file_ids = list(request.file_ids or [])
        if len(file_ids) > 10:
            raise HTTPException(status_code=400, detail="Too many file_ids (max 10)")

        # Enforce token budgets
        history = list(request.history or [])
        budget = load_token_budget()

        enhanced_logger.info(
            "CHAT_DOMAIN_RECEIVED",
            extra_data={"domain": request.domain}
        )

        # 1. Retrieve relevant chunks (RAG-lite)
        chunk_records: List[Dict[str, Any]] = []
        rag_start = time.time()
        chunk_records = await retrieve_chunk_records(
            query=request.message,
            file_ids=file_ids,
            domain=request.domain,
            top_k=5,
        )
        latency_rag = time.time() - rag_start

        # 2. Empty-context guard + relevance floor
        min_score = float(os.getenv("RAG_MIN_SCORE", "0.2"))
        if min_score > 0:
            chunk_records = [
                rec for rec in chunk_records if float(rec.get("score", 0.0)) >= min_score
            ]

        system_prompt = get_system_prompt(request.domain)
        history, chunk_records, usage = enforce_input_budget(
            system_prompt=system_prompt,
            history=history,
            user_message=request.message,
            rag_records=chunk_records,
            budget=budget,
        )
        tokens_input = usage.get("total_tokens", 0)

        rag_used = len(chunk_records) > 0
        chunks_used = len(chunk_records)

        if chunk_records:
            rag_avg_score = sum(float(r.get("score", 0.0)) for r in chunk_records) / len(chunk_records)

        rag_context = "\n\n".join(r.get("text", "") for r in chunk_records) if chunk_records else None

        # 3. Call LLM via domain router
        llm_start = time.time()
        temperature = float(os.getenv("GEMINI_TEMPERATURE", "0.2"))
        response_payload, _raw_text = await generate_domain_response(
            request.domain,
            request.message,
            rag_context=rag_context,
            history=history,
            max_output_tokens=budget.max_output_tokens,
            temperature=temperature,
        )
        latency_llm = time.time() - llm_start
        first_token_latency = latency_llm

        answer = response_payload.get("answer", "")
        follow_up_questions = response_payload.get("follow_up_questions", [])
        confidence_score = float(response_payload.get("confidence_score", 0.0))

        tokens_output = count_tokens(answer)
        tokens_output += sum(count_tokens(q) for q in follow_up_questions)

        sources: List[Dict[str, Any]] = []
        for rec in chunk_records:
            text = rec.get("text", "")
            sources.append(
                {
                    "file_id": rec.get("file_id"),
                    "chunk_id": rec.get("chunk_id"),
                    "chunk_index": rec.get("chunk_index"),
                    "domain": rec.get("domain"),
                    "score": rec.get("score", 0.0),
                    "text_preview": text[:200],
                }
            )

        latency_ms = (time.time() - start_time) * 1000.0

        return ChatResponse(
            answer=answer,
            follow_up_questions=follow_up_questions,
            sources=sources,
            confidence_score=confidence_score,
            latency_ms=round(latency_ms, 2),
        )

    except HTTPException:
        raise
    except Exception as e:
        enhanced_logger.exception(
            "CHAT_FAILED",
            exc_info=e,
            extra_data={"domain": request.domain},
        )
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        enhanced_logger.info(
            "CHAT_METRICS",
            extra_data={
                "domain": request.domain,
                "rag_used": rag_used,
                "files_used": len(request.file_ids or []),
                "chunks_used": chunks_used,
                "rag_avg_score": round(rag_avg_score, 4),
                "tokens_input": tokens_input,
                "tokens_output": tokens_output,
                "model_name": model_name,
                "first_token_latency": round(first_token_latency, 3),
                "total_latency": round(time.time() - start_time, 3),
                "latency_rag": round(latency_rag, 3),
                "latency_llm": round(latency_llm, 3),
                "fallback_used": fallback_used,
            },
        )
