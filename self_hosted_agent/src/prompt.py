"""Load system prompt from MLflow."""

import mlflow

# Remove this when we have a proper tracking URI
mlflow.set_tracking_uri("sqlite:///mlflow.db")

# Load prompt from MLflow at module level
_prompt = mlflow.genai.load_prompt("pr-review-agent-system-prompt")
SYSTEM_PROMPT = _prompt.template

#print(SYSTEM_PROMPT)