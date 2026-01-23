"""Build a JSONL eval set from FinDER for RAGAS."""

import json
from pathlib import Path
from typing import Any

import yaml
from datasets import load_dataset

CONFIG_PATH = Path("evals/ragas/config.yaml")
OUTPUT_PATH = Path("evals/ragas/eval_data.jsonl")
INVALID_REVISIONS = {"main", "master", "latest", "REPLACE_WITH_DATASET_REVISION"}


def _require_revision(revision: str | None) -> str:
    """Ensure a pinned dataset revision is provided.

    Args:
        revision: Revision string from config.

    Returns:
        The validated revision string.
    """
    if not revision or revision.strip() in INVALID_REVISIONS:
        raise SystemExit(
            "Error: dataset revision must be pinned in evals/ragas/config.yaml "
            "(set dataset.revision to a tag or commit hash)."
        )
    return revision.strip()


def load_config() -> dict[str, Any]:
    """Load the RAGAS evaluation config file.

    Returns:
        Configuration dictionary.
    """
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def pick_field(row: dict[str, Any], candidates: list[str]) -> str | None:
    """Select the first available field in a row.

    Args:
        row: Dataset row dictionary.
        candidates: Candidate field names in priority order.

    Returns:
        The chosen field name, or None if missing.
    """
    for name in candidates:
        if name in row and row[name]:
            return name
    return None


def main() -> None:
    """Build the JSONL evaluation set for RAGAS.

    Returns:
        None.
    """
    cfg = load_config()
    ds_cfg = cfg["dataset"]
    revision = _require_revision(ds_cfg.get("revision"))
    dataset = load_dataset(  # nosec B615
        ds_cfg["name"],
        split=ds_cfg["split"],
        revision=revision,
    )
    limit = min(int(ds_cfg["limit"]), len(dataset))
    dataset = dataset.select(range(limit))
    max_context_chars = int(ds_cfg.get("max_context_chars", 4000))
    max_contexts = int(ds_cfg.get("max_contexts", 4))

    question_fields = ds_cfg["question_field_candidates"]
    answer_fields = ds_cfg["answer_field_candidates"]
    context_fields = ds_cfg["context_field_candidates"]

    records = []
    for row in dataset:
        question_field = pick_field(row, question_fields)
        answer_field = pick_field(row, answer_fields)
        context_field = pick_field(row, context_fields)
        if not question_field or not answer_field:
            continue

        contexts = row.get(context_field, [])
        if isinstance(contexts, str):
            contexts = [contexts]
        trimmed_contexts = []
        for context in contexts:
            if not context:
                continue
            trimmed_contexts.append(str(context)[:max_context_chars])
            if len(trimmed_contexts) >= max_contexts:
                break

        records.append(
            {
                "question": row[question_field],
                "answer": row.get(answer_field, ""),
                "contexts": trimmed_contexts,
                "ground_truth": row.get(answer_field, ""),
            }
        )

    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")

    print(f"Wrote {len(records)} records to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
