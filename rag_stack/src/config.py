"""Configuration loader for the RAG API."""


from pathlib import Path
from typing import Any

import os
import yaml
from pydantic import BaseModel


class ChromaConfig(BaseModel):
    host: str
    port: int
    collection: str


class RetrievalConfig(BaseModel):
    top_k: int
    rerank_k: int


class ModelConfig(BaseModel):
    embedding: str
    reranker: str


class GenerationConfig(BaseModel):
    base_url: str
    model: str
    temperature: float = 0.2


class MLflowConfig(BaseModel):
    tracking_uri: str


class GuardrailConfig(BaseModel):
    hallucination_threshold: float
    jailbreak_threshold: float
    financial_advice_enabled: bool = False


class AppConfig(BaseModel):
    chroma: ChromaConfig
    retrieval: RetrievalConfig
    models: ModelConfig
    generation: GenerationConfig
    mlflow: MLflowConfig
    guardrails: GuardrailConfig


def load_config(path: str | None = None) -> AppConfig:
    """Load YAML config from disk with basic validation."""
    config_path = path or os.getenv("CONFIG_PATH", "src/config.yaml")
    data: dict[str, Any]
    with Path(config_path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return AppConfig.model_validate(data)
