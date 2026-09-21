"""Evaluation-only Hugging Face embedding provider (controlled comparison unit).

This module exists ONLY for the local retrieval representation evaluation experiment.
It is NOT the production embedding provider and is not wired into any pipeline stage.

Provider: Local sentence-transformer models evaluated on varying dimensional bases.
Credentials: None required.
"""

from __future__ import annotations
import time
from clinivault_ai.embedding.errors import EmbeddingError

class HFEmbeddingProvider:
    """Semantic embeddings via Hugging Face sentence-transformers (evaluation-only)."""

    def __init__(self, model_name: str, device: str = "cpu"):
        if not model_name:
            raise ValueError("model_name must be provided")
        self.name = model_name
        self.device = device
        
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise EmbeddingError("sentence-transformers is not installed") from exc

        # Initialize model
        t0 = time.time()
        self.model = SentenceTransformer(self.name, device=self.device)
        self.load_latency = time.time() - t0
        self.dimension = self.model.get_sentence_embedding_dimension()

    def provider_params(self) -> dict:
        return {
            "method": "hf-sentence-transformers",
            "model": self.name,
            "device": self.device,
            "dimension": self.dimension,
            "external": False,
        }

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts)

    def embed_query(self, query: str) -> list[float]:
        return self._embed([query])[0]

    def _embed(self, texts: list[str]) -> list[list[float]]:
        for text in texts:
            if not isinstance(text, str) or not text.strip():
                raise EmbeddingError("cannot embed empty or whitespace-only text")
        
        # Default batch_size for sentence_transformers is usually 32
        import torch
        with torch.no_grad():
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            
        vectors = []
        for emb in embeddings:
            vectors.append([float(v) for v in emb])
        return vectors
