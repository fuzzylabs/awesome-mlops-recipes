"""Metaflow pipeline for ingesting and indexing FinDER subset."""

from __future__ import annotations

import json
import os
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Any

import boto3
import chromadb
from bs4 import BeautifulSoup
from datasets import load_dataset
from metaflow import FlowSpec, Parameter, step, kubernetes
from sentence_transformers import SentenceTransformer
import yaml

DEFAULT_IMAGE = os.getenv("METAFLOW_KUBERNETES_IMAGE", "rag-metaflow:latest")


def load_config(path: str) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def pick_field(row: dict[str, Any], candidates: list[str]) -> str | None:
    for name in candidates:
        if name in row and row[name]:
            return name
    return None


def normalize_text(text: str) -> str:
    if "<" in text and ">" in text:
        return BeautifulSoup(text, "html.parser").get_text(" ")
    return text


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        next_start = end - chunk_overlap
        if next_start <= start:
            next_start = end
        start = next_start
    return chunks


class RagIngestFlow(FlowSpec):
    config_path = Parameter("config", default="data_pipeline/config.yaml")

    @step
    def start(self):
        self.config = load_config(self.config_path)
        self.next(self.ingest)

    @kubernetes(image=DEFAULT_IMAGE, cpu=2, memory=4096)
    @step
    def ingest(self):
        dataset_cfg = self.config["dataset"]
        dataset = load_dataset(dataset_cfg["name"], split=dataset_cfg["split"])
        limit = min(int(dataset_cfg["doc_limit"]), len(dataset))
        dataset = dataset.select(range(limit))

        docs = []
        for idx, row in enumerate(dataset):
            text_field = pick_field(row, dataset_cfg["text_field_candidates"])
            if not text_field:
                continue
            doc_id_field = pick_field(row, dataset_cfg["id_field_candidates"])
            doc_id = row.get(doc_id_field) if doc_id_field else f"doc-{idx}"
            docs.append({"id": str(doc_id), "text": row[text_field]})

        self.docs = docs
        self.next(self.parse)

    @kubernetes(image=DEFAULT_IMAGE, cpu=2, memory=4096)
    @step
    def parse(self):
        parsed = []
        for doc in self.docs:
            parsed.append({"id": doc["id"], "text": normalize_text(doc["text"])})
        self.docs = parsed
        self.next(self.chunk)

    @kubernetes(image=DEFAULT_IMAGE, cpu=2, memory=4096)
    @step
    def chunk(self):
        chunk_cfg = self.config["chunking"]
        chunks = []
        for doc in self.docs:
            doc_chunks = chunk_text(
                doc["text"],
                chunk_size=chunk_cfg["chunk_size"],
                chunk_overlap=chunk_cfg["chunk_overlap"],
            )
            for idx, chunk in enumerate(doc_chunks):
                chunks.append(
                    {
                        "id": f"{doc['id']}-{idx}",
                        "text": chunk,
                        "metadata": {"doc_id": doc["id"]},
                    }
                )
        self.chunks = chunks
        self.next(self.embed)

    @kubernetes(image=DEFAULT_IMAGE, cpu=4, memory=8192)
    @step
    def embed(self):
        embed_cfg = self.config["embeddings"]
        embedder = SentenceTransformer(embed_cfg["model"])
        self.embeddings = [embedder.encode(chunk["text"], normalize_embeddings=True).tolist() for chunk in self.chunks]
        self.next(self.index)

    @kubernetes(image=DEFAULT_IMAGE, cpu=2, memory=4096)
    @step
    def index(self):
        chroma_cfg = self.config["chroma"]
        client = chromadb.HttpClient(host=chroma_cfg["host"], port=chroma_cfg["port"])
        collection = client.get_or_create_collection(name=chroma_cfg["collection"])
        if chroma_cfg.get("rebuild"):
            existing = collection.get(include=[])
            existing_ids = existing.get("ids", [])
            if existing_ids:
                collection.delete(ids=existing_ids)
        collection.add(
            ids=[chunk["id"] for chunk in self.chunks],
            embeddings=self.embeddings,
            documents=[chunk["text"] for chunk in self.chunks],
            metadatas=[chunk["metadata"] for chunk in self.chunks],
        )
        self.next(self.snapshot)

    @kubernetes(image=DEFAULT_IMAGE, cpu=1, memory=2048)
    @step
    def snapshot(self):
        s3_cfg = self.config["s3"]
        persist_dir = os.getenv("CHROMA_PERSIST_DIR")
        if not persist_dir:
            print("CHROMA_PERSIST_DIR not set, skipping snapshot.")
            self.next(self.end)
            return

        persist_path = Path(persist_dir)
        if not persist_path.exists():
            print(f"Chroma persist dir not found: {persist_path}")
            self.next(self.end)
            return

        snapshot_name = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        archive_path = Path(f"/tmp/chroma-snapshot-{snapshot_name}.tar.gz")
        with tarfile.open(archive_path, "w:gz") as archive:
            archive.add(persist_path, arcname="chroma")

        s3 = boto3.client("s3")
        key_prefix = s3_cfg["prefix"].rstrip("/")
        key = f"{key_prefix}/{snapshot_name}.tar.gz"
        s3.upload_file(str(archive_path), s3_cfg["bucket"], key)

        self._cleanup_snapshots(s3, s3_cfg, key_prefix)
        self.next(self.end)

    def _cleanup_snapshots(self, s3, s3_cfg: dict[str, Any], key_prefix: str) -> None:
        response = s3.list_objects_v2(Bucket=s3_cfg["bucket"], Prefix=key_prefix)
        objects = response.get("Contents", [])
        objects.sort(key=lambda item: item["LastModified"], reverse=True)
        keep = int(s3_cfg.get("keep_last", 3))
        for obj in objects[keep:]:
            s3.delete_object(Bucket=s3_cfg["bucket"], Key=obj["Key"])

    @step
    def end(self):
        summary = {
            "documents": len(self.docs),
            "chunks": len(self.chunks),
        }
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    RagIngestFlow()
