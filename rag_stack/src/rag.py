"""Core retrieval and generation logic."""

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import chromadb
import mlflow
import requests
from sentence_transformers import CrossEncoder, SentenceTransformer

from src.config import AppConfig

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = (
    "You are a retrieval-augmented assistant for financial filings. "
    "Answer using only the provided context. "
    "If the answer is not supported by the context, say you do not know. "
    "Cite the most relevant chunks in your response."
)


@dataclass
class RetrievedChunk:
    """Container for retrieved chunks and metadata.

    Args:
        chunk_id: Unique identifier for the chunk.
        text: Raw chunk content.
        metadata: Metadata for the chunk.
        score: Optional reranking score.
    """

    chunk_id: str
    text: str
    metadata: dict[str, Any]
    score: float | None = None


class RagService:
    """Retrieve from Chroma and generate answers using vLLM."""

    def __init__(self, config: AppConfig) -> None:
        """Initialise the service and model clients.

        Args:
            config: Application configuration values.
        """
        self.config = config
        self._embedder = SentenceTransformer(config.models.embedding)
        self._reranker = CrossEncoder(config.models.reranker)
        self._chroma = chromadb.HttpClient(
            host=config.chroma.host,
            port=config.chroma.port,
        )
        self._collection = self._chroma.get_or_create_collection(name=config.chroma.collection)
        self._system_prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        """Load the system prompt from MLflow or fallback to the default.

        Returns:
            The prompt text to use for generation.
        """
        prompt_name = "rag-stack-system-prompt"
        try:
            mlflow.set_tracking_uri(self.config.mlflow.tracking_uri)
            prompt = mlflow.genai.load_prompt(prompt_name)
            if prompt and hasattr(prompt, "template") and prompt.template:
                return prompt.template  # type: ignore[no-any-return]
        except Exception as exc:
            logger.warning("Failed to load prompt from MLflow; using default. %s", exc)
        return DEFAULT_SYSTEM_PROMPT

    def _embed(self, text: str) -> list[float]:
        """Embed text into a dense vector representation.

        Args:
            text: Input text to embed.

        Returns:
            The embedding vector.
        """
        return self._embedder.encode(text, normalize_embeddings=True).tolist()  # type: ignore[no-any-return]

    def retrieve(self, question: str) -> tuple[list[RetrievedChunk], int]:
        """Retrieve and rerank chunks for a question.

        Args:
            question: User question to retrieve context for.

        Returns:
            A tuple of reranked chunks and the raw retrieved count.
        """
        query_embedding = self._embed(question)
        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=self.config.retrieval.top_k,
            include=["documents", "metadatas"],
        )
        retrieved_count = len(result.get("ids", [[]])[0])
        chunks: list[RetrievedChunk] = []
        for chunk_id, text, metadata in zip(
            result.get("ids", [[]])[0],
            result.get("documents", [[]])[0],
            result.get("metadatas", [[]])[0],
        ):
            chunks.append(
                RetrievedChunk(
                    chunk_id=str(chunk_id),
                    text=text,
                    metadata=metadata or {},
                )
            )
        return self._rerank(question, chunks), retrieved_count

    def _rerank(self, question: str, chunks: Iterable[RetrievedChunk]) -> list[RetrievedChunk]:
        """Rerank retrieved chunks using a cross-encoder.

        Args:
            question: Question used for scoring.
            chunks: Retrieved chunks to rerank.

        Returns:
            The top reranked chunks.
        """
        chunk_list = list(chunks)
        if not chunk_list:
            return []
        pairs = [[question, chunk.text] for chunk in chunk_list]
        scores = self._reranker.predict(pairs)
        for chunk, score in zip(chunk_list, scores):
            chunk.score = float(score)
        chunk_list.sort(key=lambda item: item.score or 0.0, reverse=True)
        return chunk_list[: self.config.retrieval.rerank_k]

    def answer(self, question: str) -> dict[str, Any]:
        """Answer a question using retrieved context.

        Args:
            question: User question to answer.

        Returns:
            The response payload with answer and metadata.
        """
        chunks, retrieved_count = self.retrieve(question)
        context_block = self._format_context(chunks)
        user_prompt = (
            f"Question:\n{question}\n\n"
            f"Context:\n{context_block}\n\n"
            "Provide a concise answer with citations."
        )
        response = self._call_vllm(user_prompt)
        return {
            "answer": response,
            "chunks": [chunk.__dict__ for chunk in chunks],
            "retrieved_count": retrieved_count,
            "reranked_count": len(chunks),
        }

    def _format_context(self, chunks: Iterable[RetrievedChunk]) -> str:
        """Format chunks into a single context block.

        Args:
            chunks: Chunks to format.

        Returns:
            The formatted context string.
        """
        parts = []
        for chunk in chunks:
            parts.append(f"[chunk_id={chunk.chunk_id}]\n{chunk.text}")
        return "\n\n".join(parts)

    def _call_vllm(self, user_prompt: str) -> str:
        """Invoke the vLLM chat completion endpoint.

        Args:
            user_prompt: User prompt to send to the model.

        Returns:
            The model response text.
        """
        payload = {
            "model": self.config.generation.model,
            "messages": [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.config.generation.temperature,
        }
        response = requests.post(
            f"{self.config.generation.base_url}/chat/completions",
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()  # type: ignore[no-any-return]
