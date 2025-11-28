"""Configuration management for the PR review agent."""

from pathlib import Path
from typing import Literal
import yaml
from pydantic import BaseModel, Field
import os


class OllamaConfig(BaseModel):
    """Ollama model configuration."""
    model_name: str = "Qwen/Qwen3-4B-Thinking-2507"
    base_url: str = "http://localhost:8000/v1"


class VLLMConfig(BaseModel):
    """vLLM model configuration."""
    model_name: str = "Qwen/Qwen3-4B-Thinking-2507"
    base_url: str = "http://localhost:8000/v1"


class ModelConfig(BaseModel):
    """Model configuration."""
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    vllm: VLLMConfig = Field(default_factory=VLLMConfig)


class MLflowConfig(BaseModel):
    """MLflow configuration."""
    tracking_uri: str = "http://localhost:5000"
    prompt_name: str = "pr-review-agent-system-prompt"
    prompt_version: str = ""  # Leave empty for latest version


class LogfireConfig(BaseModel):
    """Logfire configuration."""
    token: str = os.getenv("LOGFIRE_TOKEN", "")
    if not token:
        raise ValueError("LOGFIRE_TOKEN environment variable is not set")


class GitHubConfig(BaseModel):
    """GitHub configuration."""
    token: str = os.getenv("GITHUB_TOKEN", "")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable is not set")

class Config(BaseModel):
    """Main configuration."""
    model: ModelConfig = Field(default_factory=ModelConfig)
    mlflow: MLflowConfig = Field(default_factory=MLflowConfig)
    logfire: LogfireConfig = Field(default_factory=LogfireConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)


def load_config(config_path: str | Path | None = None) -> Config:
    """Load configuration from YAML file.
    
    Args:
        config_path: Path to config.yaml file. If None, looks in src/config.yaml
        
    Returns:
        Config object
    """
    if config_path is None:
        # Default to config.yaml in the same directory as this file
        config_path = Path(__file__).parent / "config.yaml"
    
    config_path = Path(config_path)
    
    if not config_path.exists():
        # Return default config if file doesn't exist
        return Config()
    
    with open(config_path, 'r') as f:
        config_dict = yaml.safe_load(f)
    
    return Config(**config_dict)


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance.
    
    Returns:
        Config object (singleton)
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config() -> Config:
    """Reload configuration from file.
    
    Returns:
        Newly loaded Config object
    """
    global _config
    _config = load_config()
    return _config

