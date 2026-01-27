"""Prometheus metrics for the RAG API."""

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

REQUEST_COUNT = Counter(
    "rag_requests_total",
    "Total RAG requests",
    ["status"],
)

REQUEST_LATENCY = Histogram(
    "rag_request_latency_seconds",
    "RAG request latency in seconds",
    buckets=(0.1, 0.25, 0.5, 1, 2, 5, 10, 30, 60),
)

RETRIEVED_CHUNKS = Histogram(
    "rag_retrieved_chunks",
    "Number of retrieved chunks per request",
    buckets=(1, 2, 4, 8, 12, 16, 24, 32),
)

RERANKED_CHUNKS = Histogram(
    "rag_reranked_chunks",
    "Number of reranked chunks per request",
    buckets=(1, 2, 4, 8, 12, 16),
)

GUARDRAIL_FAILURES = Counter(
    "rag_guardrail_failures_total",
    "Guardrail failures",
    ["rule"],
)


def metrics_response() -> Response:
    """Build a Prometheus metrics HTTP response.

    Returns:
        Starlette response with the latest metrics payload.
    """
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
