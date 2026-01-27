"""Create a new prompt in MLflow prompt registry."""

import mlflow


def create_new_prompt(prompt_name: str, initial_template: str) -> None:
    """Create a new prompt in MLflow prompt registry.

    Args:
        prompt_name: Name of the prompt to register.
        initial_template: Template text for the prompt.

    Returns:
        None.
    """
    mlflow.set_tracking_uri("http://localhost:5000")

    new_prompt = mlflow.genai.register_prompt(
        name=prompt_name,
        template=initial_template,
        commit_message="New prompt",
    )
    print(f"New prompt created: {new_prompt.name}")


if __name__ == "__main__":
    prompt_name = "rag-stack-system-prompt"
    initial_template = (
        "You are a retrieval-augmented assistant for financial filings. "
        "Answer using only the provided context. "
        "If the answer is not supported by the context, say you do not know. "
        "Cite the most relevant chunks in your response."
    )

    create_new_prompt(prompt_name, initial_template)
