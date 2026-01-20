"""Run RAGAS evaluation against a prepared dataset."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import mlflow
from datasets import Dataset
from openai import OpenAI
from ragas import evaluate
from ragas.embeddings import HuggingFaceEmbeddings
from ragas.llms import llm_factory
from ragas.metrics import answer_correctness, context_precision, context_recall, faithfulness

DATA_PATH = Path("evals/ragas/eval_data.jsonl")
_GUARDRAIL_ENV = "RUN_FINANCIAL_ADVICE_GUARDRAIL"


def _load_app_config():
    try:
        from src.config import load_config

        return load_config()
    except Exception:
        try:
            repo_root = Path(__file__).resolve().parents[2]
            if str(repo_root) not in sys.path:
                sys.path.insert(0, str(repo_root))
            from src.config import load_config

            return load_config()
        except Exception:
            return None


def _build_llm():
    config = _load_app_config()
    model = os.getenv("RAGAS_LLM_MODEL") or (
        config.generation.model if config else "gpt-4o-mini"
    )
    base_url = os.getenv("RAGAS_LLM_BASE_URL") or os.getenv("MODEL_BASE_URL") or (
        config.generation.base_url if config else "http://localhost:8000/v1"
    )
    api_key = os.getenv("OPENAI_API_KEY", "local")
    client = OpenAI(api_key=api_key, base_url=base_url)
    return llm_factory(model, client=client)


def _build_embeddings():
    config = _load_app_config()
    model = os.getenv("RAGAS_EMBEDDING_MODEL") or (
        config.models.embedding if config else "BAAI/bge-large-en-v1.5"
    )
    device = os.getenv("RAGAS_EMBEDDING_DEVICE")
    return HuggingFaceEmbeddings(model=model, device=device or None)


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
    llm = _build_llm()
    embeddings = _build_embeddings()
    metrics = [context_precision, context_recall, faithfulness, answer_correctness]
    results = evaluate(dataset, metrics=metrics, llm=llm, embeddings=embeddings)
    metrics_dict = {key: float(value) for key, value in results._repr_dict.items()}
    mlflow.log_metrics(metrics_dict)
    print(metrics_dict)
    if _should_run_financial_advice_guardrail():
        from evals.guardrails.financial_advice import main as run_financial_guardrail

        run_financial_guardrail()


if __name__ == "__main__":
    main()
