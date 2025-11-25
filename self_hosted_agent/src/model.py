"""Model configuration for the PR review agent."""

import os
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.providers.anthropic import AnthropicProvider


def get_ollama_model():
    """Get Ollama model instance (lazy initialisation)."""
    return OpenAIChatModel(
        model_name='qwen3:4b-thinking-2507-fp16',
        provider=OllamaProvider(base_url='http://localhost:11434/v1'),
    )


def get_anthropic_model():
    """Get Anthropic Claude model for PR reviews."""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable must be set. "
            "Get your API key from https://console.anthropic.com/"
        )
    return AnthropicModel(
        'claude-sonnet-4-5',
        provider=AnthropicProvider(api_key=api_key)
    )

