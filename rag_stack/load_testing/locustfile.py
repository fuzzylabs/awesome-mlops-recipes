"""Locust workload for the RAG API."""

import secrets

from locust import HttpUser, between, task

QUESTIONS = [
    "Delta in CBOE Data & Access Solutions rev from 2021-23.",
    "What is the total revenue for 2023?",
    "Summarise the risk factors section for the company.",
    "What was net income in 2022?",
]


class RagUser(HttpUser):  # type: ignore[misc]
    """Locust user that submits RAG queries."""

    wait_time = between(1, 3)

    @task  # type: ignore[untyped-decorator]
    def query(self) -> None:
        """Submit a query request to the RAG API.

        Returns:
            None.
        """
        question = secrets.choice(QUESTIONS)
        self.client.post("/query", json={"question": question})
