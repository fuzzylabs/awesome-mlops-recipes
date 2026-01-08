"""Simple hallucination guardrail checks against the RAG API."""

from __future__ import annotations

import json
import os
from pathlib import Path

import mlflow
import requests

DATA_PATH = Path("evals/guardrails/hallucination_cases.jsonl")
API_URL = os.getenv("RAG_API_URL", "http://localhost:8080/query")


def is_refusal(answer: str) -> bool:
    lowered = answer.lower()
    return "do not know" in lowered or "not in the context" in lowered


def main() -> None:
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Missing {DATA_PATH}. Create JSONL with question and must_refuse fields."
        )

    total = 0
    passed = 0
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            question = record["question"]
            must_refuse = bool(record.get("must_refuse", False))

            response = requests.post(API_URL, json={"question": question}, timeout=120)
            response.raise_for_status()
            answer = response.json()["answer"]

            ok = is_refusal(answer) if must_refuse else not is_refusal(answer)
            total += 1
            if ok:
                passed += 1

    pass_rate = passed / max(total, 1)
    mlflow.log_metric("hallucination_pass_rate", pass_rate)
    print({"total": total, "passed": passed, "pass_rate": pass_rate})


if __name__ == "__main__":
    main()
