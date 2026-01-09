"""Locust workload for the RAG API."""

from __future__ import annotations

import random

from locust import HttpUser, between, task


QUESTIONS = [
    "Delta in CBOE Data & Access Solutions rev from 2021-23.",
    "What is the total revenue for 2023?",
    "Summarise the risk factors section for the company.",
    "What was net income in 2022?",
]


class RagUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def query(self) -> None:
        question = random.choice(QUESTIONS)
        self.client.post("/query", json={"question": question})
