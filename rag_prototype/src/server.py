"""FastAPI server for the RAG prototype."""

from __future__ import annotations

import time

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.config import load_config
from src.rag import RagService
from src.metrics import (
    GUARDRAIL_FAILURES,
    REQUEST_COUNT,
    REQUEST_LATENCY,
    RETRIEVED_CHUNKS,
    RERANKED_CHUNKS,
    metrics_response,
)


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    chunks: list[dict]


app = FastAPI(title="RAG Prototype", version="0.1.0")

config = load_config()
rag_service = RagService(config)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return metrics_response()


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question is required")
    start = time.perf_counter()
    try:
        result = rag_service.answer(request.question)
        REQUEST_COUNT.labels(status="success").inc()
    except Exception:
        REQUEST_COUNT.labels(status="error").inc()
        raise
    finally:
        REQUEST_LATENCY.observe(time.perf_counter() - start)

    retrieved = result.get("retrieved_count", 0)
    reranked = result.get("reranked_count", 0)
    if retrieved:
        RETRIEVED_CHUNKS.observe(retrieved)
    if reranked:
        RERANKED_CHUNKS.observe(reranked)
    GUARDRAIL_FAILURES.labels(rule="none").inc(0)

    return QueryResponse(answer=result["answer"], chunks=result["chunks"])
