"""Create a new prompt in MLFlow prompt registry."""

import mlflow


def create_new_prompt(prompt_name: str, initial_template: str):
    """Create a new prompt in MLFlow prompt registry."""
    mlflow.set_tracking_uri("http://localhost:5000")

    new_prompt = mlflow.genai.register_prompt(
        name=prompt_name,
        template=initial_template,
        commit_message="New prompt",
    )
    print(f"New prompt created: {new_prompt.name}")

    return new_prompt


if __name__ == "__main__":
    prompt_name = "pr-review-agent-system-prompt"
    initial_template = "You are an expert pull request reviewer."

    create_new_prompt(prompt_name, initial_template)