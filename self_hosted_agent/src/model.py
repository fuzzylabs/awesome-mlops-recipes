"""Model configuration for the PR review agent."""

import os
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.providers.anthropic import AnthropicProvider
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


def get_anthropic_model():
    """Get Anthropic Claude model from config."""
    cfg = get_config()
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable must be set. "
            "Get your API key from https://console.anthropic.com/"
        )
    return AnthropicModel(
        cfg.model.anthropic.model_name,
        provider=AnthropicProvider(api_key=api_key)
    )


def get_model():
    """Get the configured model based on config.yaml provider setting."""
    cfg = get_config()
    
    if cfg.model.provider == "anthropic":
        return get_anthropic_model()
    elif cfg.model.provider == "vllm":
        return get_vllm_model()
    elif cfg.model.provider == "ollama":
        return get_ollama_model()
    else:
        raise ValueError(f"Unknown model provider: {cfg.model.provider}")

