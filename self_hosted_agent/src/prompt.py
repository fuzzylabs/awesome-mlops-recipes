"""Load system prompt from MLflow."""

import mlflow
from config import get_config


def load_prompt() -> tuple[str, str | int]:
    """Load the system prompt from MLflow.

    Returns:
        tuple[str, str | int]: Prompt template and prompt version.
    """
    cfg = get_config()
    mlflow.set_tracking_uri(cfg.mlflow.tracking_uri)

    _prompt = mlflow.genai.load_prompt(
        cfg.mlflow.prompt_name,
        version=cfg.mlflow.prompt_version or None,  # None for latest version
    )

    return _prompt.template, _prompt.version
