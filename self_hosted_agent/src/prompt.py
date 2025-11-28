"""Load system prompt from MLflow."""

import mlflow
from config import get_config


def load_prompt():
    """Load prompt from MLflow."""
    cfg = get_config()
    mlflow.set_tracking_uri(cfg.mlflow.tracking_uri)

    _prompt = mlflow.genai.load_prompt(
        cfg.mlflow.prompt_name,
        version=cfg.mlflow.prompt_version or None # None for latest version
    )

    return _prompt.template, _prompt.version
