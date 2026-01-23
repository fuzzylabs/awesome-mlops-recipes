"""FastAPI server for the RAG stack."""

import time
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.config import load_config
from src.guardrails import apply_financial_advice_guardrail
from src.metrics import (
    GUARDRAIL_FAILURES,
    REQUEST_COUNT,
    REQUEST_LATENCY,
    RERANKED_CHUNKS,
    RETRIEVED_CHUNKS,
    metrics_response,
)
from src.rag import RagService


class QueryRequest(BaseModel):  # type: ignore[misc]
    """Request payload for RAG queries.

    Args:
        question: User question string.
    """

    question: str


class QueryResponse(BaseModel):  # type: ignore[misc]
    """Response payload for RAG queries.

    Args:
        answer: Model-generated answer.
        chunks: Retrieved chunk payloads.
    """

    answer: str
    chunks: list[dict[str, Any]]


app = FastAPI(title="RAG Stack", version="0.1.0")

config = load_config()
rag_service = RagService(config)


@app.get("/health")  # type: ignore[untyped-decorator]
def health() -> dict[str, str]:
    """Report service health.

    Returns:
        Simple status payload.
    """
    return {"status": "ok"}


@app.get("/metrics")  # type: ignore[untyped-decorator]
def metrics() -> Any:
    """Expose Prometheus metrics.

    Returns:
        Metrics response payload.
    """
    return metrics_response()


@app.post("/query", response_model=QueryResponse)  # type: ignore[untyped-decorator]
def query(request: QueryRequest) -> QueryResponse:
    """Answer a RAG query and emit metrics.

    Args:
        request: Query request payload.

    Returns:
        Structured query response.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question is required")
    start = time.perf_counter()
    blocked = False
    try:
        result = rag_service.answer(request.question)
        if config.guardrails.financial_advice_enabled:
            guarded_answer, blocked = apply_financial_advice_guardrail(
                request.question, result["answer"]
            )
            result["answer"] = guarded_answer
            if blocked:
                result["chunks"] = []
                GUARDRAIL_FAILURES.labels(rule="financial_advice").inc()
                REQUEST_COUNT.labels(status="blocked").inc()
            else:
                REQUEST_COUNT.labels(status="success").inc()
        else:
            REQUEST_COUNT.labels(status="success").inc()
    except Exception:
        REQUEST_COUNT.labels(status="error").inc()
        raise
    finally:
        REQUEST_LATENCY.observe(time.perf_counter() - start)

    if not blocked:
        retrieved = result.get("retrieved_count", 0)
        reranked = result.get("reranked_count", 0)
        if retrieved:
            RETRIEVED_CHUNKS.observe(retrieved)
        if reranked:
            RERANKED_CHUNKS.observe(reranked)
    GUARDRAIL_FAILURES.labels(rule="none").inc(0)

    return QueryResponse(answer=result["answer"], chunks=result["chunks"])
