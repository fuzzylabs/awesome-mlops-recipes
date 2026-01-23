"""Configuration loader for the RAG API."""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel


class ChromaConfig(BaseModel):  # type: ignore[misc]
    """Chroma connection settings.

    Args:
        host: Chroma host address.
        port: Chroma service port.
        collection: Collection name.
    """

    host: str
    port: int
    collection: str


class RetrievalConfig(BaseModel):  # type: ignore[misc]
    """Retrieval configuration values.

    Args:
        top_k: Number of chunks to retrieve.
        rerank_k: Number of chunks to keep after reranking.
    """

    top_k: int
    rerank_k: int


class ModelConfig(BaseModel):  # type: ignore[misc]
    """Embedding and reranker model identifiers.

    Args:
        embedding: Embedding model name.
        reranker: Reranker model name.
    """

    embedding: str
    reranker: str


class GenerationConfig(BaseModel):  # type: ignore[misc]
    """Generation settings for the LLM endpoint.

    Args:
        base_url: Base URL for the model server.
        model: Model name to use.
        temperature: Sampling temperature.
    """

    base_url: str
    model: str
    temperature: float = 0.2


class MLflowConfig(BaseModel):  # type: ignore[misc]
    """MLflow tracking settings.

    Args:
        tracking_uri: MLflow tracking URI.
    """

    tracking_uri: str


class GuardrailConfig(BaseModel):  # type: ignore[misc]
    """Guardrail thresholds and toggles.

    Args:
        hallucination_threshold: Threshold for hallucination scores.
        jailbreak_threshold: Threshold for jailbreak scores.
        financial_advice_enabled: Whether to enable the finance guardrail.
    """

    hallucination_threshold: float
    jailbreak_threshold: float
    financial_advice_enabled: bool = False


class AppConfig(BaseModel):  # type: ignore[misc]
    """Top-level application configuration.

    Args:
        chroma: Chroma connection settings.
        retrieval: Retrieval settings.
        models: Model identifiers.
        generation: Generation settings.
        mlflow: MLflow tracking settings.
        guardrails: Guardrail settings.
    """

    chroma: ChromaConfig
    retrieval: RetrievalConfig
    models: ModelConfig
    generation: GenerationConfig
    mlflow: MLflowConfig
    guardrails: GuardrailConfig


def load_config(path: str | None = None) -> AppConfig:
    """Load YAML configuration from disk.

    Args:
        path: Optional path to the config file.

    Returns:
        The validated application configuration.
    """
    config_path = path or os.getenv("CONFIG_PATH", "src/config.yaml") or "src/config.yaml"
    data: dict[str, Any]
    with Path(config_path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return AppConfig.model_validate(data)  # type: ignore[no-any-return]
