"""Metaflow pipeline for ingesting and indexing 10-K filings."""

import json
from pathlib import Path
from typing import Any

import chromadb
import yaml
from bs4 import BeautifulSoup
from fetch_10k import fetch_sample_10k_filings
from metaflow import FlowSpec, Parameter, step
from sentence_transformers import SentenceTransformer


def load_config(path: str) -> dict[str, Any]:
    """Load the pipeline configuration from YAML.

    Args:
        path: Path to the YAML config file.

    Returns:
        Configuration dictionary.
    """
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_local_10k_filings(directory: str) -> list[dict[str, Any]]:
    """Load 10-K filings from a local directory.

    Args:
        directory: Directory containing filings and metadata.

    Returns:
        List of document dictionaries.
    """
    docs = []
    dir_path = Path(directory)

    # Load metadata if available
    metadata_path = dir_path / "metadata.json"
    metadata = {}
    if metadata_path.exists():
        with metadata_path.open() as f:
            for item in json.load(f):
                metadata[item.get("filepath", "")] = item

    # Load text files
    for filepath in sorted(dir_path.glob("*.txt")):
        text = filepath.read_text(encoding="utf-8")
        meta = metadata.get(str(filepath), {})
        docs.append(
            {
                "id": meta.get("id", filepath.stem),
                "text": text,
                "company": meta.get("company", filepath.stem),
                "ticker": meta.get("ticker", ""),
                "filing_date": meta.get("filing_date", ""),
            }
        )

    return docs


def normalize_text(text: str) -> str:
    """Normalize text by stripping HTML when detected.

    Args:
        text: Raw text content.

    Returns:
        Cleaned text content.
    """
    if "<" in text and ">" in text:
        return BeautifulSoup(text, "html.parser").get_text(" ")  # type: ignore[no-any-return]
    return text


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Split text into overlapping word chunks.

    Args:
        text: Source text to split.
        chunk_size: Number of words per chunk.
        chunk_overlap: Number of overlapping words between chunks.

    Returns:
        List of text chunks.
    """
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


class RagIngestFlow(FlowSpec):  # type: ignore[misc]
    """Metaflow pipeline for ingesting and indexing filings."""

    config_path = Parameter("config", default="data_pipeline/config.yaml")

    @step  # type: ignore[untyped-decorator]
    def start(self) -> None:
        """Load configuration and start the flow.

        Returns:
            None.
        """
        self.config = load_config(self.config_path)
        self.next(self.fetch)

    @step  # type: ignore[untyped-decorator]
    def fetch(self) -> None:
        """Fetch filings when configured to do so.

        Returns:
            None.
        """
        dataset_cfg = self.config["dataset"]
        if dataset_cfg.get("fetch_on_start", False):
            source_dir = dataset_cfg.get("source_dir", "data_pipeline/10k_filings")
            fetch_count = int(dataset_cfg.get("fetch_count", 3))
            print(f"Fetching {fetch_count} 10-K filings into {source_dir}...")
            fetch_sample_10k_filings(output_dir=source_dir, num_companies=fetch_count)
        self.next(self.ingest)

    @step  # type: ignore[untyped-decorator]
    def ingest(self) -> None:
        """Load filings from the configured source directory.

        Returns:
            None.
        """
        dataset_cfg = self.config["dataset"]
        source_dir = dataset_cfg.get("source_dir", "data_pipeline/10k_filings")

        docs = load_local_10k_filings(source_dir)

        # Apply limit if specified
        limit = dataset_cfg.get("doc_limit")
        if limit and limit < len(docs):
            docs = docs[:limit]

        print(f"Loaded {len(docs)} documents from {source_dir}")
        for doc in docs:
            print(f"  - {doc['id']}: {doc.get('company', 'Unknown')} ({len(doc['text']):,} chars)")

        self.docs = docs
        self.next(self.parse)

    @step  # type: ignore[untyped-decorator]
    def parse(self) -> None:
        """Normalize text for each document.

        Returns:
            None.
        """
        parsed = []
        for doc in self.docs:
            parsed.append({"id": doc["id"], "text": normalize_text(doc["text"])})
        self.docs = parsed
        self.next(self.chunk)

    @step  # type: ignore[untyped-decorator]
    def chunk(self) -> None:
        """Split documents into overlapping chunks.

        Returns:
            None.
        """
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

    @step  # type: ignore[untyped-decorator]
    def embed(self) -> None:
        """Embed chunks using the configured model.

        Returns:
            None.
        """
        embed_cfg = self.config["embeddings"]
        embedder = SentenceTransformer(embed_cfg["model"])
        self.embeddings = [
            embedder.encode(chunk["text"], normalize_embeddings=True).tolist()
            for chunk in self.chunks
        ]
        self.next(self.index_chunks)

    @step  # type: ignore[untyped-decorator]
    def index_chunks(self) -> None:
        """Index chunks in Chroma.

        Returns:
            None.
        """
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
        self.next(self.end)

    @step  # type: ignore[untyped-decorator]
    def end(self) -> None:
        """Print a summary of the ingest process.

        Returns:
            None.
        """
        summary = {
            "documents": len(self.docs),
            "chunks": len(self.chunks),
        }
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    RagIngestFlow()
