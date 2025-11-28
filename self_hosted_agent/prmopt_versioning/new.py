"""Create a new prompt in MLFlow prompt registry."""

import mlflow

PROMPT_NAME = "pr-review-agent-system-prompt"

initial_template = "You are an expert pull request reviewer for the fuzzylabs/sre-agent repository."

# Remote/Local MLflow
mlflow.set_tracking_uri("http://localhost:5000")


new_prompt = mlflow.genai.register_prompt(
    name=PROMPT_NAME,
    template=initial_template,
    commit_message="New prompt",
)

print(f"New prompt created: {new_prompt.name}")