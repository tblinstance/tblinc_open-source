"""3. RAGEngine: Hybrid BM25 + TF-IDF cosine retrieval-augmented generation engine."""

from __future__ import annotations

import math
import re
import time
from collections import Counter
from typing import Any

from ..core import BaseAIModel, ModelMetadata, PredictionResult, register_model, timed_predict

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has",
    "in", "is", "it", "of", "on", "or", "that", "the", "to", "was", "with",
}


def _terms(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9_]+", text.lower()) if t not in _STOPWORDS and len(t) > 1]


@register_model
class RAGEngine(BaseAIModel):
    """Document chunking, hybrid BM25 + TF-IDF cosine indexing, and grounded synthesis."""

    metadata = ModelMetadata(
        key="search",
        name="Knowledge Search (RAG)",
        category="RAG & Search",
        task="Retrieval-Augmented Generation",
        description="Chunks documents, indexes with BM25 + TF-IDF cosine vectors, and synthesizes cited answers.",
        input_example={"query": "How does tblinc generate an admin panel?", "top_k": 2},
        tags=["rag", "bm25", "tfidf", "search", "retrieval"],
    )

    def __init__(self, chunk_size: int = 240, k1: float = 1.5, b: float = 0.75) -> None:
        super().__init__()
        self.chunk_size = max(60, chunk_size)
        self.k1 = k1
        self.b = b
        self.chunks: list[dict[str, Any]] = []
        self.doc_freq: dict[str, int] = {}
        self.avg_dl: float = 1.0

    def _chunk_doc(self, text: str, source: str) -> list[dict[str, Any]]:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        chunks: list[dict[str, Any]] = []
        buf = ""
        for sent in sentences:
            if buf and len(buf) + len(sent) + 1 > self.chunk_size:
                chunks.append({"source": source, "text": buf.strip(), "tokens": _terms(buf)})
                buf = sent
            else:
                buf = f"{buf} {sent}".strip()
        if buf:
            chunks.append({"source": source, "text": buf.strip(), "tokens": _terms(buf)})
        return chunks

    def fit(self, documents: list[str | dict[str, str]]) -> RAGEngine:
        self.chunks = []
        for idx, doc in enumerate(documents):
            if isinstance(doc, dict):
                source = doc.get("source", f"doc_{idx + 1}")
                text = doc.get("text", "")
            else:
                source = f"doc_{idx + 1}"
                text = str(doc)
            self.chunks.extend(self._chunk_doc(text, source))

        if not self.chunks:
            raise ValueError("RAG corpus cannot be empty.")

        df: Counter[str] = Counter()
        total_len = 0
        for ch in self.chunks:
            toks = ch["tokens"]
            total_len += len(toks)
            for term in set(toks):
                df[term] += 1

        self.doc_freq = dict(df)
        self.avg_dl = max(1.0, total_len / len(self.chunks))
        self.is_fitted = True
        self.trained_at = time.time()
        self.training_metrics = {
            "documents": len(documents),
            "chunks_indexed": len(self.chunks),
            "unique_terms": len(self.doc_freq),
        }
        return self

    def _idf(self, term: str) -> float:
        n = len(self.chunks)
        df = self.doc_freq.get(term, 0)
        return math.log((n - df + 0.5) / (df + 0.5) + 1.0)

    def _score_chunk(self, q_terms: list[str], chunk: dict[str, Any]) -> float:
        toks = chunk["tokens"]
        if not toks or not q_terms:
            return 0.0
        tf = Counter(toks)
        dl = len(toks)
        bm25 = 0.0
        for term in q_terms:
            f = tf.get(term, 0)
            if f == 0:
                continue
            idf = self._idf(term)
            denom = f + self.k1 * (1.0 - self.b + self.b * (dl / self.avg_dl))
            bm25 += idf * ((f * (self.k1 + 1.0)) / denom)

        # TF-IDF cosine component
        q_vec = {t: (q_terms.count(t) * self._idf(t)) for t in set(q_terms)}
        d_vec = {t: (c * self._idf(t)) for t, c in tf.items()}
        dot = sum(q_vec[t] * d_vec.get(t, 0.0) for t in q_vec)
        q_norm = math.sqrt(sum(v * v for v in q_vec.values())) or 1.0
        d_norm = math.sqrt(sum(v * v for v in d_vec.values())) or 1.0
        cosine = dot / (q_norm * d_norm)
        return 0.65 * bm25 + 0.35 * (cosine * 4.0)

    @timed_predict
    def predict(self, data: str | dict[str, Any], top_k: int = 3) -> PredictionResult:
        if not self.is_fitted:
            raise RuntimeError("RAGEngine must be fitted with documents before predict().")
        if isinstance(data, dict):
            query = str(data.get("query", ""))
            top_k = int(data.get("top_k", top_k))
        else:
            query = str(data)

        q_terms = _terms(query)
        scored = [
            (self._score_chunk(q_terms, ch), ch)
            for ch in self.chunks
        ]
        scored.sort(key=lambda item: item[0], reverse=True)
        hits = [
            {"source": ch["source"], "score": round(score, 4), "text": ch["text"]}
            for score, ch in scored[: max(1, top_k)]
            if score > 0.0
        ]

        if not hits:
            answer = "No matching context found in the indexed knowledge base."
            conf = 0.0
        else:
            snippets = [f"[{h['source']}] {h['text']}" for h in hits]
            answer = " ".join(snippets)
            conf = min(0.99, round(hits[0]["score"] / (hits[0]["score"] + 1.0), 4))

        return PredictionResult(
            model=self.metadata.key,
            prediction=answer,
            confidence=conf,
            details={"query": query, "hits": hits},
        )

    def get_state(self) -> dict[str, Any]:
        return {
            "chunk_size": self.chunk_size,
            "k1": self.k1,
            "b": self.b,
            "chunks": self.chunks,
            "doc_freq": self.doc_freq,
            "avg_dl": self.avg_dl,
        }

    def set_state(self, state: dict[str, Any]) -> None:
        self.chunk_size = int(state["chunk_size"])
        self.k1 = float(state["k1"])
        self.b = float(state["b"])
        self.chunks = list(state["chunks"])
        self.doc_freq = dict(state["doc_freq"])
        self.avg_dl = float(state["avg_dl"])

    def _run_demo(self, custom_input: Any = None) -> dict[str, Any]:
        docs = [
            {
                "source": "admin_guide.md",
                "text": "The tblinc AdminSite automatically inspects registered ORM models and generates a ready-to-use CRUD admin panel styled with Tailwind CSS, Lucide icons, and Motion animations.",
            },
            {
                "source": "architecture.md",
                "text": "tblinc is a standalone Python MTV/MVC web framework built without Django, Flask, or FastAPI, featuring SQLite ORM, custom templates, forms, CSRF protection, and authentication.",
            },
            {
                "source": "ai_catalog.md",
                "text": "The tblinc ai_models package includes 25 built-in AI models covering Causal Multi-Head Transformers, Neural DDPM Diffusion, MLP, RAG, Vision CNN, Random Forest, Gradient Boosting, Isolation Forest, Forecasting, Recommendations, Voice TTS, and Music synthesis.",
            },
        ]
        self.fit(docs)
        res = self.predict(custom_input or self.metadata.input_example)
        return {"training": self.training_metrics, "result": res.to_dict()}
