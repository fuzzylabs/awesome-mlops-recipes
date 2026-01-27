"""Configuration management for the PR review agent."""

import os
from functools import cached_property
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field


class OllamaConfig(BaseModel):  # type: ignore[misc]
    """Ollama model configuration.

    Args:
        model_name: Ollama model name.
        base_url: Base URL for the Ollama endpoint.
    """

    model_name: str = "Qwen/Qwen3-4B-Thinking-2507"
    base_url: str = "http://localhost:8000/v1"


class VLLMConfig(BaseModel):  # type: ignore[misc]
    """vLLM model configuration.

    Args:
        model_name: vLLM model name.
        base_url: Base URL for the vLLM endpoint.
    """

    model_name: str = "Qwen/Qwen3-4B-Thinking-2507"
    base_url: str = "http://localhost:8000/v1"


class ModelConfig(BaseModel):  # type: ignore[misc]
    """Model configuration.

    Args:
        provider: Model provider name.
        ollama: Ollama configuration.
        vllm: vLLM configuration.
    """

    provider: Literal["ollama", "vllm"] = "vllm"
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    vllm: VLLMConfig = Field(default_factory=VLLMConfig)


class MLflowConfig(BaseModel):  # type: ignore[misc]
    """MLflow configuration.

    Args:
        tracking_uri: MLflow tracking URI.
        prompt_name: Prompt registry name.
        prompt_version: Prompt version to load.
    """

    tracking_uri: str = "http://localhost:5000"
    prompt_name: str = "pr-review-agent-system-prompt"
    prompt_version: str = ""  # Leave empty for latest version


class LogfireConfig(BaseModel):  # type: ignore[misc]
    """Logfire configuration.

    Args:
        traces_endpoint: OTLP traces endpoint URL.
    """

    traces_endpoint: str = os.getenv(
        "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
        "http://localhost:4318/v1/traces",
    )

    @cached_property
    def env(self) -> dict[str, str]:
        """Build environment variables for OTLP tracing.

        Returns:
            dict[str, str]: Environment variable mapping.
        """
        return {
            "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT": self.traces_endpoint,
        }


class GitHubConfig(BaseModel):  # type: ignore[misc]
    """GitHub configuration.

    Args:
        token: GitHub API token.
    """

    token: str = os.getenv("GITHUB_TOKEN", "")


class MCPConfig(BaseModel):  # type: ignore[misc]
    """MCP gateway configuration.

    Args:
        gateway_url: Optional MCP gateway URL.
        gateway_auth_token: Auth token for the gateway.
        gateway_forward_github_token: Whether to forward GitHub auth.
        github_mcp_url: GitHub MCP server URL.
    """

    gateway_url: str | None = None
    gateway_auth_token: str = os.getenv("MCP_GATEWAY_TOKEN", "")
    gateway_forward_github_token: bool = True
    github_mcp_url: str = "https://api.githubcopilot.com/mcp/"


class Config(BaseModel):  # type: ignore[misc]
    """Main configuration container.

    Args:
        model: Model configuration.
        mlflow: MLflow configuration.
        logfire: Logfire configuration.
        github: GitHub configuration.
        mcp: MCP configuration.
    """

    model: ModelConfig = Field(default_factory=ModelConfig)
    mlflow: MLflowConfig = Field(default_factory=MLflowConfig)
    logfire: LogfireConfig = Field(default_factory=LogfireConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)


def load_config(config_path: str | Path | None = None) -> Config:
    """Load configuration from YAML file.

    Args:
        config_path: Optional path to the config file.

    Returns:
        Config: Loaded configuration object.
    """
    if config_path is None:
        # Default to config.yaml in the same directory as this file
        config_path = Path(__file__).parent / "config.yaml"

    config_path = Path(config_path)

    if not config_path.exists():
        # Return default config if file doesn't exist
        return Config()

    with open(config_path) as f:
        config_dict = yaml.safe_load(f)

    return Config(**config_dict)


# Global config container (mutable to avoid global statement)
_config_container: dict[str, Config] = {}


def get_config() -> Config:
    """Get the global configuration instance.

    Returns:
        Config: Singleton configuration instance.
    """
    if "instance" not in _config_container:
        _config_container["instance"] = load_config()
    return _config_container["instance"]


def reload_config() -> Config:
    """Reload configuration from file.

    Returns:
        Config: Newly loaded configuration instance.
    """
    _config_container["instance"] = load_config()
    return _config_container["instance"]
