"""Fetch feedback from Postgres or fallback to sample data."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import psycopg


SAMPLE_PATH = Path("feedback_loop/sample_feedback.jsonl")


def fetch_feedback(limit: int = 50) -> list[dict[str, Any]]:
    dsn = os.getenv("FEEDBACK_DB_DSN")
    if not dsn:
        return _load_sample_feedback(limit)

    query = (
        "SELECT question, answer, rating, comment, created_at "
        "FROM rag_feedback ORDER BY created_at DESC LIMIT %s"
    )
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (limit,))
            rows = cur.fetchall()

    return [
        {
            "question": row[0],
            "answer": row[1],
            "rating": row[2],
            "comment": row[3],
            "created_at": str(row[4]),
        }
        for row in rows
    ]


def _load_sample_feedback(limit: int) -> list[dict[str, Any]]:
    if not SAMPLE_PATH.exists():
        return []
    records: list[dict[str, Any]] = []
    with SAMPLE_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
            if len(records) >= limit:
                break
    return records
