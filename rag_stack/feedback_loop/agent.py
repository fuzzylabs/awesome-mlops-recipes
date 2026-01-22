"""Feedback loop agent using Pydantic AI to propose prompt updates."""


import os
from typing import Any

import mlflow
from mlflow import MlflowClient
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from feedback_loop.feedback_store import fetch_feedback


SYSTEM_PROMPT = """
You are a prompt engineer improving a RAG system prompt based on user feedback.

Your tasks:
1. Analyse feedback for errors, missing citations, or unsafe responses.
2. Identify patterns and propose concise, concrete prompt changes.
3. Output the updated prompt only.

Do not include commentary or analysis in the final output.
""".strip()


def get_model() -> OpenAIChatModel:
    model_name = os.getenv("MODEL_NAME", "Qwen/Qwen3-4B-Thinking-2507")
    base_url = os.getenv(
        "MODEL_BASE_URL",
        "http://rayserve-vllm-serve-svc.rayserve.svc.cluster.local:8000/v1",
    )
    os.environ.setdefault("OPENAI_API_KEY", "local")
    return OpenAIChatModel(
        model_name=model_name,
        provider=OpenAIProvider(base_url=base_url),
    )


def load_prompt(prompt_name: str) -> str:
    prompt = mlflow.genai.load_prompt(prompt_name)
    return prompt.template if prompt and prompt.template else ""


def register_proposed_prompt(prompt_name: str, new_prompt: str, summary: str) -> None:
    proposed = mlflow.genai.register_prompt(
        name=prompt_name,
        template=new_prompt,
        commit_message="status=proposed",
    )

    client = MlflowClient()
    try:
        client.set_prompt_tag(proposed.name, "status", "proposed")
        client.set_prompt_tag(proposed.name, "feedback_summary", summary[:512])
    except AttributeError:
        with mlflow.start_run(run_name="proposed-prompt"):
            mlflow.set_tags({"status": "proposed", "prompt_name": proposed.name})
            mlflow.log_text(summary, "feedback_summary.txt")
            mlflow.log_text(new_prompt, "proposed_prompt.txt")


def main() -> None:
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))

    prompt_name = os.getenv("PROMPT_NAME", "rag-stack-system-prompt")
    current_prompt = load_prompt(prompt_name)

    feedback = fetch_feedback()
    if not feedback:
        print("No feedback found. Exiting.")
        return

    summary = "\n".join(
        f"Q: {item['question']}\nA: {item['answer']}\nRating: {item.get('rating')}\nComment: {item.get('comment')}\n"
        for item in feedback
    )

    agent = Agent(get_model(), system_prompt=SYSTEM_PROMPT)
    user_prompt = (
        "Current prompt:\n"
        f"{current_prompt}\n\n"
        "Feedback:\n"
        f"{summary}\n\n"
        "Return the updated prompt only."
    )
    result = agent.run_sync(user_prompt)
    new_prompt = result.output.strip()

    register_proposed_prompt(prompt_name, new_prompt, summary)
    print("Proposed prompt registered in MLflow.")


if __name__ == "__main__":
    main()
