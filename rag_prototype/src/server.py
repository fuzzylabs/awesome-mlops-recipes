"""FastAPI server for the RAG prototype."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.config import load_config
from src.rag import RagService


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


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question is required")
    result = rag_service.answer(request.question)
    return QueryResponse(answer=result["answer"], chunks=result["chunks"])
