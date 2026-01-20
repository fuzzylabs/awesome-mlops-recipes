"""Simple jailbreak guardrail checks against the RAG API."""


import json
import os
from pathlib import Path

import mlflow
import requests
from guardrails import Guard

from evals.guardrails.validators import JailbreakRefusalValidator


DATA_PATH = Path("evals/guardrails/jailbreak_cases.jsonl")
API_URL = os.getenv("RAG_API_URL", "http://localhost:8080/query")


def main() -> None:
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Missing {DATA_PATH}. Create JSONL with question field."
        )

    guard = Guard().use(JailbreakRefusalValidator)
    total = 0
    passed = 0
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            question = record["question"]

            response = requests.post(API_URL, json={"question": question}, timeout=120)
            response.raise_for_status()
            answer = response.json()["answer"]

            outcome = guard.validate(answer, metadata={})
            ok = outcome.validation_passed
            total += 1
            if ok:
                passed += 1

    pass_rate = passed / max(total, 1)
    mlflow.log_metric("jailbreak_pass_rate", pass_rate)
    print({"total": total, "passed": passed, "pass_rate": pass_rate})


if __name__ == "__main__":
    main()
