"""Approve a proposed prompt version in MLflow."""

from __future__ import annotations

import os

import mlflow
from mlflow import MlflowClient


def main() -> None:
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))

    prompt_name = os.getenv("PROMPT_NAME", "rag-stack-system-prompt")
    status = os.getenv("PROMPT_STATUS", "approved")

    client = MlflowClient()
    try:
        client.set_prompt_tag(prompt_name, "status", status)
        client.set_prompt_tag(prompt_name, "stage", "production")
        print(f"Prompt {prompt_name} tagged as {status}.")
    except AttributeError:
        with mlflow.start_run(run_name="approve-prompt"):
            mlflow.set_tags({"status": status, "prompt_name": prompt_name, "stage": "production"})
        print("Recorded approval in MLflow run tags.")


if __name__ == "__main__":
    main()
