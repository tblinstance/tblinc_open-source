"""11. KNNModel: Distance-weighted K-Nearest Neighbors classifier & regressor."""

from __future__ import annotations

import math
import time
from collections import defaultdict
from typing import Any

from ..core import BaseAIModel, ModelMetadata, PredictionResult, register_model, timed_predict


@register_model
class KNNModel(BaseAIModel):
    """K-Nearest Neighbors model supporting Euclidean, Manhattan, and Cosine metrics."""

    metadata = ModelMetadata(
        key="similarity",
        name="Similarity Matcher",
        category="Tabular / ML",
        task="Instance-Based Classification",
        description="Distance-weighted K-Nearest Neighbors with Euclidean, Manhattan, and Cosine metrics.",
        input_example={"features": [2.1, 1.9]},
        tags=["knn", "similarity", "classification", "vector"],
    )

    def __init__(self, k: int = 3, metric: str = "euclidean") -> None:
        super().__init__()
        self.k = max(1, k)
        self.metric = metric
        self.X_train: list[list[float]] = []
        self.y_train: list[Any] = []

    def _distance(self, a: list[float], b: list[float]) -> float:
        if self.metric == "manhattan":
            return sum(abs(x - y) for x, y in zip(a, b))
        if self.metric == "cosine":
            dot = sum(x * y for x, y in zip(a, b))
            na = math.sqrt(sum(x * x for x in a)) or 1.0
            nb = math.sqrt(sum(y * y for y in b)) or 1.0
            return 1.0 - (dot / (na * nb))
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

    def fit(self, X: list[list[float]], y: list[Any]) -> KNNModel:
        if not X or len(X) != len(y):
            raise ValueError("X and y must be non-empty and match in length.")
        self.X_train = [[float(v) for v in row] for row in X]
        self.y_train = list(y)
        self.is_fitted = True
        self.trained_at = time.time()
        self.training_metrics = {
            "samples_indexed": len(self.X_train),
            "k": self.k,
            "metric": self.metric,
        }
        return self

    @timed_predict
    def predict(self, data: list[float] | dict[str, Any]) -> PredictionResult:
        if not self.is_fitted:
            raise RuntimeError("KNNModel must be fitted before predict().")
        features = data["features"] if isinstance(data, dict) else data
        vec = [float(v) for v in features]
        scored = sorted(
            ((self._distance(vec, row), lbl) for row, lbl in zip(self.X_train, self.y_train)),
            key=lambda item: item[0],
        )
        neighbors = scored[: min(self.k, len(scored))]
        weights: dict[Any, float] = defaultdict(float)
        for dist, lbl in neighbors:
            weights[lbl] += 1.0 / (dist + 1e-6)
        total_w = sum(weights.values()) or 1.0
        best_lbl = max(weights, key=lambda k: weights[k])
        return PredictionResult(
            model=self.metadata.key,
            prediction=best_lbl,
            confidence=round(weights[best_lbl] / total_w, 4),
            details={
                "neighbors": [{"label": lbl, "distance": round(d, 4)} for d, lbl in neighbors],
            },
        )

    def evaluate(self, X: list[list[float]], y: list[Any]) -> dict[str, Any]:
        correct = sum(1 for xi, yi in zip(X, y) if self.predict(xi).prediction == yi)
        return {"accuracy": round(correct / max(1, len(y)), 4), "samples": len(y)}

    def get_state(self) -> dict[str, Any]:
        return {"k": self.k, "metric": self.metric, "X_train": self.X_train, "y_train": self.y_train}

    def set_state(self, state: dict[str, Any]) -> None:
        self.k = int(state["k"])
        self.metric = str(state["metric"])
        self.X_train = state["X_train"]
        self.y_train = state["y_train"]

    def _run_demo(self, custom_input: Any = None) -> dict[str, Any]:
        X = [
            [1.0, 1.2], [1.8, 2.0], [2.2, 1.7],
            [8.0, 7.5], [8.5, 8.2], [7.8, 8.4],
            [1.5, 8.5], [2.0, 8.1], [1.2, 7.9],
        ]
        y = [
            "zone_alpha", "zone_alpha", "zone_alpha",
            "zone_beta", "zone_beta", "zone_beta",
            "zone_gamma", "zone_gamma", "zone_gamma",
        ]
        self.fit(X, y)
        res = self.predict(custom_input or self.metadata.input_example)
        return {"training": self.training_metrics, "result": res.to_dict()}
