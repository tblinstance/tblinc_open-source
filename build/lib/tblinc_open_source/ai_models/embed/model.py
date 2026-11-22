"""21. EmbeddingModel: Dense L2-normalized Subword + TF-IDF Text Embedding & Semantic Similarity Engine."""

from __future__ import annotations

import hashlib
import math
import re
import time
from typing import Any

from ..core import BaseAIModel, ModelMetadata, PredictionResult, register_model, timed_predict

_TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "")]


def _char_ngrams(word: str, n: int = 3) -> list[str]:
    padded = f"<{word}>"
    if len(padded) < n:
        return [padded]
    return [padded[i : i + n] for i in range(len(padded) - n + 1)]


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


@register_model
class EmbeddingModel(BaseAIModel):
    """Dense vector encoder mapping text into L2-normalized word + character-3gram embeddings for semantic search."""

    metadata = ModelMetadata(
        key="embed",
        name="Text Embedding Engine",
        category="Vector & Search",
        task="Dense Vector Embeddings & Semantic Similarity",
        description="Encodes text into fixed-size L2-normalized dense embeddings with subword hashing & IDF weighting.",
        input_example={"text": "pure python ai web framework", "top_k": 2},
        tags=["embeddings", "vectors", "semantic-search", "rag"],
    )

    def __init__(self, dim: int = 32) -> None:
        super().__init__()
        self.dim = max(8, dim)
        self.idf: dict[str, float] = {}
        self.corpus_texts: list[str] = []
        self.corpus_vectors: list[list[float]] = []

    def encode(self, text: str) -> list[float]:
        return self._encode_vec(text)

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        return [self._encode_vec(t) for t in texts]

    def _hash_add(self, vec: list[float], token: str, weight: float) -> None:
        h = hashlib.sha256(token.encode("utf-8")).digest()
        idx1 = int.from_bytes(h[:2], "big") % self.dim
        idx2 = int.from_bytes(h[2:4], "big") % self.dim
        sign1 = 1.0 if (h[4] & 1) == 0 else -1.0
        sign2 = 1.0 if (h[5] & 1) == 0 else -1.0
        vec[idx1] += sign1 * weight
        vec[idx2] += sign2 * weight * 0.5

    def _encode_vec(self, text: str) -> list[float]:
        tokens = _tokenize(text)
        vec = [0.0] * self.dim
        if not tokens:
            return vec
        tf: dict[str, int] = {}
        for tok in tokens:
            tf[tok] = tf.get(tok, 0) + 1
        for tok, count in tf.items():
            weight = (1.0 + math.log(count)) * self.idf.get(tok, 1.5)
            self._hash_add(vec, tok, weight)
            # Subword character 3-grams capture morphological similarity (e.g. train / training / trainer)
            if len(tok) >= 4:
                ngrams = _char_ngrams(tok, 3)
                sub_w = (weight * 0.25) / max(1, len(ngrams))
                for ng in ngrams:
                    self._hash_add(vec, f"ng:{ng}", sub_w)
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [round(v / norm, 5) for v in vec]

    def fit(self, texts: list[str]) -> EmbeddingModel:
        if not texts:
            raise ValueError("texts must be a non-empty list of strings.")
        n = len(texts)
        df: dict[str, int] = {}
        for doc in texts:
            for tok in set(_tokenize(doc)):
                df[tok] = df.get(tok, 0) + 1
        self.idf = {tok: math.log((n + 1.0) / (cnt + 1.0)) + 1.0 for tok, cnt in df.items()}
        self.corpus_texts = list(texts)
        self.corpus_vectors = [self._encode_vec(doc) for doc in texts]
        self.is_fitted = True
        self.trained_at = time.time()
        self.training_metrics = {
            "documents": n,
            "vocab_size": len(self.idf),
            "embedding_dim": self.dim,
        }
        return self

    @timed_predict
    def predict(self, data: str | dict[str, Any]) -> PredictionResult:
        if not self.is_fitted:
            raise RuntimeError("EmbeddingModel must be fitted before predict().")
        if isinstance(data, dict):
            text = str(data.get("text", "")).strip()
            top_k = max(1, int(data.get("top_k", 3)))
        else:
            text = str(data).strip()
            top_k = 3

        vec = self._encode_vec(text)
        scored = [
            {"text": doc, "similarity": round(_cosine(vec, cvec), 4)}
            for doc, cvec in zip(self.corpus_texts, self.corpus_vectors)
        ]
        scored.sort(key=lambda item: item["similarity"], reverse=True)
        top_matches = scored[:top_k]
        best_sim = max(0.0, min(1.0, (top_matches[0]["similarity"] + 1.0) / 2.0)) if top_matches else 0.0
        return PredictionResult(
            model=self.metadata.key,
            prediction=vec,
            confidence=round(best_sim, 4),
            details={
                "dim": self.dim,
                "norm": round(math.sqrt(sum(v * v for v in vec)), 4),
                "nearest": top_matches,
            },
        )

    def get_state(self) -> dict[str, Any]:
        return {
            "dim": self.dim,
            "idf": self.idf,
            "corpus_texts": self.corpus_texts,
            "corpus_vectors": self.corpus_vectors,
        }

    def set_state(self, state: dict[str, Any]) -> None:
        self.dim = int(state["dim"])
        self.idf = {str(k): float(v) for k, v in state["idf"].items()}
        self.corpus_texts = list(state["corpus_texts"])
        self.corpus_vectors = [[float(x) for x in row] for row in state["corpus_vectors"]]

    def _run_demo(self, custom_input: Any = None) -> dict[str, Any]:
        docs = [
            "tblinc is a pure python AI and standalone MTV/MVC web framework.",
            "Train custom diffusion image generators and voice models inside the admin panel.",
            "Manage API keys, token quotas, and SQLite ORM models with Light and Dark themes.",
            "Detect anomalies, forecast sales trends, and run gradient boosting on tabular data.",
        ]
        self.fit(docs)
        res = self.predict(custom_input or self.metadata.input_example)
        return {"training": self.training_metrics, "result": res.to_dict()}
