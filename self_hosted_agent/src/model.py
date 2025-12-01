"""Model configuration for the PR review agent."""

import os
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.providers.openai import OpenAIProvider

from config import get_config


def get_ollama_model():
    """Get Ollama model instance from config."""
    cfg = get_config()
    return OpenAIChatModel(
        model_name=cfg.model.ollama.model_name,
        provider=OllamaProvider(base_url=cfg.model.ollama.base_url),
    )


def get_vllm_model():
    """Get vLLM model instance from config."""
    cfg = get_config()
    return OpenAIChatModel(
        model_name=cfg.model.vllm.model_name,
        provider=OpenAIProvider(base_url=cfg.model.vllm.base_url),
    )


def get_model():
    """Get the configured model based on config.yaml provider setting."""
    cfg = get_config()
    
    if cfg.model.provider == "vllm":
        return get_vllm_model()
    elif cfg.model.provider == "ollama":
        return get_ollama_model()
    else:
        raise ValueError(f"Unknown model provider: {cfg.model.provider}. Supported providers: vllm, ollama")

