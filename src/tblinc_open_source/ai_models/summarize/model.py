"""23. TextSummarizerModel: TextRank Graph Centrality + TF-IDF Extractive Summarizer & Keyword Extractor."""

from __future__ import annotations

import math
import re
import time
from typing import Any

from ..core import BaseAIModel, ModelMetadata, PredictionResult, register_model, timed_predict

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "in",
    "is", "it", "of", "on", "or", "that", "the", "to", "was", "were", "will", "with",
}
_WORD_RE = re.compile(r"[a-zA-Z0-9_]+")
_SENT_RE = re.compile(r"(?<=[.!?])\s+")


def _words(text: str) -> list[str]:
    return [w.lower() for w in _WORD_RE.findall(text or "") if w.lower() not in _STOPWORDS and len(w) > 2]


@register_model
class TextSummarizerModel(BaseAIModel):
    """Extractive NLP summarizer combining TextRank sentence graph centrality with corpus TF-IDF salience."""

    metadata = ModelMetadata(
        key="summarize",
        name="Text Summarizer AI",
        category="LLM / NLP",
        task="Extractive Document Summarization & Keywords",
        description="Distills long articles into key sentences via TextRank PageRank centrality + TF-IDF keywords.",
        input_example={
            "text": (
                "tblinc is a standalone pure Python AI and MTV/MVC web framework with zero external core dependencies. "
                "It includes 25 modular built-in AI models covering chat, images, video, audio, voice, music, and tabular ML. "
                "The auto-generated admin panel provides full CRUD tables, live model training, API key management, and token quotas. "
                "Developers can launch a responsive Light and Dark AI web app in seconds using tblinc serve."
            ),
            "max_sentences": 2,
        },
        tags=["summarization", "nlp", "textrank", "keywords"],
    )

    def __init__(self, damping: float = 0.85, iterations: int = 15) -> None:
        super().__init__()
        self.damping = damping
        self.iterations = iterations
        self.idf: dict[str, float] = {}

    def fit(self, documents: list[str]) -> TextSummarizerModel:
        if not documents:
            raise ValueError("documents must be a non-empty list of strings.")
        n = len(documents)
        df: dict[str, int] = {}
        for doc in documents:
            for tok in set(_words(doc)):
                df[tok] = df.get(tok, 0) + 1
        self.idf = {tok: math.log((n + 1.0) / (cnt + 1.0)) + 1.0 for tok, cnt in df.items()}
        self.is_fitted = True
        self.trained_at = time.time()
        self.training_metrics = {"corpus_docs": n, "vocab_size": len(self.idf), "damping": self.damping}
        return self

    def _textrank_scores(self, sent_tokens: list[list[str]]) -> list[float]:
        n = len(sent_tokens)
        if n <= 1:
            return [1.0] * n
        sim = [[0.0] * n for _ in range(n)]
        for i in range(n):
            set_i = set(sent_tokens[i])
            if not set_i:
                continue
            for j in range(i + 1, n):
                set_j = set(sent_tokens[j])
                if not set_j:
                    continue
                overlap = sum(self.idf.get(w, 1.0) for w in (set_i & set_j))
                denom = math.log(len(sent_tokens[i]) + 1.0) + math.log(len(sent_tokens[j]) + 1.0)
                val = overlap / max(1.0, denom)
                sim[i][j] = val
                sim[j][i] = val

        scores = [1.0 / n] * n
        row_sums = [sum(sim[i]) for i in range(n)]
        for _ in range(self.iterations):
            next_scores = [(1.0 - self.damping) / n] * n
            for i in range(n):
                for j in range(n):
                    if i != j and row_sums[j] > 1e-9:
                        next_scores[i] += self.damping * (sim[j][i] / row_sums[j]) * scores[j]
            scores = next_scores
        mx = max(scores, default=1.0) or 1.0
        return [s / mx for s in scores]

    @timed_predict
    def predict(self, data: str | dict[str, Any]) -> PredictionResult:
        if not self.is_fitted:
            raise RuntimeError("TextSummarizerModel must be fitted before predict().")
        if isinstance(data, dict):
            text = str(data.get("text", "")).strip()
            max_sentences = max(1, int(data.get("max_sentences", 2)))
        else:
            text = str(data).strip()
            max_sentences = 2

        sentences = [s.strip() for s in _SENT_RE.split(text) if s.strip()]
        if not sentences:
            return PredictionResult(model=self.metadata.key, prediction="", confidence=0.0, details={"keywords": []})

        word_freq: dict[str, float] = {}
        for w in _words(text):
            word_freq[w] = word_freq.get(w, 0.0) + self.idf.get(w, 1.2)
        max_f = max(word_freq.values(), default=1.0)
        norm_scores = {w: v / max_f for w, v in word_freq.items()}

        sent_toks = [_words(s) for s in sentences]
        tr_scores = self._textrank_scores(sent_toks)

        ranked: list[tuple[int, float, str]] = []
        for idx, (sent, ws, tr) in enumerate(zip(sentences, sent_toks, tr_scores)):
            if not ws:
                continue
            tfidf_score = sum(norm_scores.get(w, 0.2) for w in ws) / len(ws)
            lead_bonus = 1.12 if idx == 0 else 1.0
            combined = (0.55 * tfidf_score + 0.45 * tr) * lead_bonus
            ranked.append((idx, combined, sent))

        ranked.sort(key=lambda item: item[1], reverse=True)
        chosen = sorted(ranked[:max_sentences], key=lambda item: item[0])
        summary = " ".join(item[2] for item in chosen)
        keywords = [w for w, _ in sorted(word_freq.items(), key=lambda kv: kv[1], reverse=True)[:6]]
        compression = round(len(summary) / max(1, len(text)), 3)
        conf = round(min(0.99, 0.72 + (chosen[0][1] * 0.25 if chosen else 0.0)), 4)

        return PredictionResult(
            model=self.metadata.key,
            prediction=summary,
            confidence=conf,
            details={
                "keywords": keywords,
                "original_sentences": len(sentences),
                "summary_sentences": len(chosen),
                "compression_ratio": compression,
            },
        )

    def get_state(self) -> dict[str, Any]:
        return {"damping": self.damping, "iterations": self.iterations, "idf": self.idf}

    def set_state(self, state: dict[str, Any]) -> None:
        self.damping = float(state.get("damping", 0.85))
        self.iterations = int(state.get("iterations", 15))
        self.idf = {str(k): float(v) for k, v in state["idf"].items()}

    def _run_demo(self, custom_input: Any = None) -> dict[str, Any]:
        corpus = [
            "Pure Python web frameworks simplify deployment with zero external dependencies.",
            "AI platforms combine chat, diffusion image generation, video synthesis, voice, and music.",
            "Admin panels manage users, database records, model training runs, API keys, and token quotas.",
        ]
        self.fit(corpus)
        res = self.predict(custom_input or self.metadata.input_example)
        return {"training": self.training_metrics, "result": res.to_dict()}
