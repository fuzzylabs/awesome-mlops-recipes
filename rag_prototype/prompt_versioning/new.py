"""Create a new prompt in MLflow prompt registry."""

import mlflow


def create_new_prompt(prompt_name: str, initial_template: str):
    """Create a new prompt in MLflow prompt registry."""
    mlflow.set_tracking_uri("http://localhost:5000")

    new_prompt = mlflow.genai.register_prompt(
        name=prompt_name,
        template=initial_template,
        commit_message="New prompt",
    )
    print(f"New prompt created: {new_prompt.name}")

    return new_prompt


if __name__ == "__main__":
    prompt_name = "rag-prototype-system-prompt"
    initial_template = (
        "You are a retrieval-augmented assistant for financial filings. "
        "Answer using only the provided context. "
        "If the answer is not supported by the context, say you do not know. "
        "Do not provide financial advice or investment recommendations. "
        "Cite the most relevant chunks in your response."
    )

    create_new_prompt(prompt_name, initial_template)
