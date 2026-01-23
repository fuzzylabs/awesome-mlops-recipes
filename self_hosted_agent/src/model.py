"""Model configuration for the PR review agent."""

from config import get_config
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.providers.openai import OpenAIProvider


def get_ollama_model() -> OpenAIChatModel:
    """Build the Ollama-backed model from config.

    Returns:
        OpenAIChatModel: Configured OpenAIChatModel instance.
    """
    cfg = get_config()
    return OpenAIChatModel(
        model_name=cfg.model.ollama.model_name,
        provider=OllamaProvider(base_url=cfg.model.ollama.base_url),
    )


def get_vllm_model() -> OpenAIChatModel:
    """Build the vLLM-backed model from config.

    Returns:
        OpenAIChatModel: Configured OpenAIChatModel instance.
    """
    cfg = get_config()
    return OpenAIChatModel(
        model_name=cfg.model.vllm.model_name,
        provider=OpenAIProvider(base_url=cfg.model.vllm.base_url),
    )


def get_model() -> OpenAIChatModel:
    """Get the configured model based on provider setting.

    Returns:
        OpenAIChatModel: Configured OpenAIChatModel instance.
    """
    cfg = get_config()

    if cfg.model.provider == "vllm":
        return get_vllm_model()
    elif cfg.model.provider == "ollama":
        return get_ollama_model()
    else:
        raise ValueError(
            f"Unknown model provider: {cfg.model.provider}. Supported providers: vllm, ollama"
        )
