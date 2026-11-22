"""4. NaiveBayesTextClassifier: Multinomial Naive Bayes NLP sentiment & intent classifier."""

from __future__ import annotations

import math
import re
import time
from collections import Counter, defaultdict
from typing import Any

from ..core import BaseAIModel, ModelMetadata, PredictionResult, register_model, timed_predict


def _extract_ngrams(text: str, ngram_range: tuple[int, int] = (1, 2)) -> list[str]:
    words = re.findall(r"[a-z0-9']+", text.lower())
    feats: list[str] = []
    lo, hi = ngram_range
    for n in range(lo, hi + 1):
        for i in range(len(words) - n + 1):
            feats.append("_".join(words[i : i + n]))
    return feats


@register_model
class NaiveBayesTextClassifier(BaseAIModel):
    """Laplace-smoothed Multinomial Naive Bayes classifier with unigram + bigram features."""

    metadata = ModelMetadata(
        key="sentiment",
        name="Sentiment Analyzer",
        category="LLM / NLP",
        task="Sentiment & Intent Classification",
        description="Unigram+bigram Multinomial Naive Bayes classifier with calibrated log-probabilities.",
        input_example={"text": "This AI framework is fast, clean, and awesome!"},
        tags=["nlp", "sentiment", "intent", "naive-bayes"],
    )

    def __init__(self, alpha: float = 1.0, ngram_range: tuple[int, int] = (1, 2)) -> None:
        super().__init__()
        self.alpha = alpha
        self.ngram_range = list(ngram_range)
        self.class_priors: dict[str, float] = {}
        self.token_counts: dict[str, dict[str, int]] = {}
        self.class_totals: dict[str, int] = {}
        self.vocab: list[str] = []

    def fit(self, texts: list[str], labels: list[str]) -> NaiveBayesTextClassifier:
        if not texts or len(texts) != len(labels):
            raise ValueError("texts and labels must be non-empty and equal length.")

        label_counts = Counter(labels)
        total_docs = len(labels)
        self.class_priors = {lbl: cnt / total_docs for lbl, cnt in label_counts.items()}

        counts: dict[str, Counter[str]] = defaultdict(Counter)
        vocab_set: set[str] = set()
        for text, lbl in zip(texts, labels):
            feats = _extract_ngrams(text, (self.ngram_range[0], self.ngram_range[1]))
            counts[lbl].update(feats)
            vocab_set.update(feats)

        self.vocab = sorted(vocab_set)
        self.token_counts = {lbl: dict(cnt) for lbl, cnt in counts.items()}
        self.class_totals = {lbl: sum(cnt.values()) for lbl, cnt in counts.items()}
        self.is_fitted = True
        self.trained_at = time.time()
        acc = self.evaluate(texts, labels)["accuracy"]
        self.training_metrics = {
            "classes": sorted(self.class_priors),
            "vocab_size": len(self.vocab),
            "train_accuracy": acc,
        }
        return self

    @timed_predict
    def predict(self, data: str | dict[str, Any]) -> PredictionResult:
        if not self.is_fitted:
            raise RuntimeError("NaiveBayesTextClassifier must be fitted before predict().")
        text = str(data.get("text", "")) if isinstance(data, dict) else str(data)
        feats = _extract_ngrams(text, (self.ngram_range[0], self.ngram_range[1]))
        v_size = max(1, len(self.vocab))

        log_scores: dict[str, float] = {}
        for lbl, prior in self.class_priors.items():
            score = math.log(max(prior, 1e-12))
            denom = self.class_totals[lbl] + self.alpha * v_size
            tmap = self.token_counts[lbl]
            for feat in feats:
                score += math.log((tmap.get(feat, 0) + self.alpha) / denom)
            log_scores[lbl] = score

        max_s = max(log_scores.values())
        exps = {lbl: math.exp(s - max_s) for lbl, s in log_scores.items()}
        norm = sum(exps.values()) or 1.0
        probs = {lbl: round(val / norm, 4) for lbl, val in exps.items()}
        best_lbl = max(probs, key=lambda k: probs[k])
        return PredictionResult(
            model=self.metadata.key,
            prediction=best_lbl,
            confidence=probs[best_lbl],
            details={"probabilities": probs, "feature_count": len(feats)},
        )

    def evaluate(self, texts: list[str], labels: list[str]) -> dict[str, Any]:
        correct = sum(1 for t, y in zip(texts, labels) if self.predict(t).prediction == y)
        return {"accuracy": round(correct / max(1, len(labels)), 4), "samples": len(labels)}

    def get_state(self) -> dict[str, Any]:
        return {
            "alpha": self.alpha,
            "ngram_range": self.ngram_range,
            "class_priors": self.class_priors,
            "token_counts": self.token_counts,
            "class_totals": self.class_totals,
            "vocab": self.vocab,
        }

    def set_state(self, state: dict[str, Any]) -> None:
        self.alpha = float(state["alpha"])
        self.ngram_range = list(state["ngram_range"])
        self.class_priors = dict(state["class_priors"])
        self.token_counts = {k: dict(v) for k, v in state["token_counts"].items()}
        self.class_totals = dict(state["class_totals"])
        self.vocab = list(state["vocab"])

    def _run_demo(self, custom_input: Any = None) -> dict[str, Any]:
        texts = [
            "Love this toolkit, super fast and reliable!",
            "Awesome developer experience and clean admin UI.",
            "Great accuracy and effortless pip installation.",
            "Terrible crash, slow performance and broken builds.",
            "Worst documentation, frustrating errors everywhere.",
            "Bad bugs and unstable pipeline failures.",
            "The server runs on port 8000 using sqlite.",
            "Documentation describes models, views, and templates.",
        ]
        labels = [
            "positive", "positive", "positive",
            "negative", "negative", "negative",
            "neutral", "neutral",
        ]
        self.fit(texts, labels)
        res = self.predict(custom_input or self.metadata.input_example)
        return {"training": self.training_metrics, "result": res.to_dict()}
