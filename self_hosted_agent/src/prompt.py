"""Load system prompt from MLflow."""

import mlflow
from config import get_config

# Load config and set MLflow tracking URI
cfg = get_config()
mlflow.set_tracking_uri(cfg.mlflow.tracking_uri)

# Load prompt from MLflow at module level with specified version
_prompt = mlflow.genai.load_prompt(
    cfg.mlflow.prompt_name,
    version=cfg.mlflow.prompt_version or None # None for latest version
)
SYSTEM_PROMPT = _prompt.template
PROMPT_VERSION = str(_prompt.version)
