"""Run RAGAS evaluation against a prepared dataset."""

from __future__ import annotations

import json
import os
from pathlib import Path

import mlflow
from ragas import evaluate
from ragas.metrics import answer_correctness, context_precision, context_recall, faithfulness
from datasets import Dataset

DATA_PATH = Path("evals/ragas/eval_data.jsonl")
_GUARDRAIL_ENV = "RUN_FINANCIAL_ADVICE_GUARDRAIL"


def load_eval_dataset() -> Dataset:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Missing {DATA_PATH}. Create a JSONL file with question, answer, contexts, ground_truth."
        )
    records = []
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            records.append(json.loads(line))
    return Dataset.from_list(records)


def _should_run_financial_advice_guardrail() -> bool:
    flag = os.getenv(_GUARDRAIL_ENV, "")
    return flag.lower() in {"1", "true", "yes"}


def main() -> None:
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    dataset = load_eval_dataset()
    metrics = [context_precision, context_recall, faithfulness, answer_correctness]
    results = evaluate(dataset, metrics=metrics)
    metrics_dict = {key: float(value) for key, value in results.items()}
    mlflow.log_metrics(metrics_dict)
    print(metrics_dict)
    if _should_run_financial_advice_guardrail():
        from evals.guardrails.financial_advice import main as run_financial_guardrail

        run_financial_guardrail()


if __name__ == "__main__":
    main()
