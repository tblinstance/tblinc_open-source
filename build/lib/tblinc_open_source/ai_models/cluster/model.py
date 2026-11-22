"""10. KMeansClusterer: Unsupervised K-Means++ clustering with inertia & silhouette score."""

from __future__ import annotations

import math
import random
import time
from typing import Any

from ..core import BaseAIModel, ModelMetadata, PredictionResult, register_model, timed_predict


def _dist_sq(a: list[float], b: list[float]) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b))


@register_model
class KMeansClusterer(BaseAIModel):
    """K-Means++ unsupervised clustering with inertia and silhouette quality scoring."""

    metadata = ModelMetadata(
        key="cluster",
        name="Smart Data Clustering",
        category="Unsupervised ML",
        task="Customer / Vector Clustering",
        description="K-Means++ initialization with Lloyd updates, inertia tracking, and silhouette evaluation.",
        input_example={"features": [12.5, 82.0]},
        tags=["clustering", "unsupervised", "kmeans"],
    )

    def __init__(self, k: int = 3, max_iter: int = 50, seed: int = 42) -> None:
        super().__init__()
        self.k = max(1, k)
        self.max_iter = max_iter
        self.seed = seed
        self.centroids: list[list[float]] = []

    def _init_kmeans_pp(self, xs: list[list[float]], rng: random.Random) -> list[list[float]]:
        centroids = [xs[rng.randrange(len(xs))][:]]
        while len(centroids) < min(self.k, len(xs)):
            dists = [min(_dist_sq(p, c) for c in centroids) for p in xs]
            total = sum(dists)
            if total <= 1e-12:
                centroids.append(xs[rng.randrange(len(xs))][:])
                continue
            r = rng.random() * total
            acc = 0.0
            chosen = xs[-1]
            for p, d in zip(xs, dists):
                acc += d
                if acc >= r:
                    chosen = p
                    break
            centroids.append(chosen[:])
        return centroids

    def fit(self, X: list[list[float]]) -> KMeansClusterer:
        if not X:
            raise ValueError("X cannot be empty.")
        xs = [[float(v) for v in row] for row in X]
        d = len(xs[0])
        rng = random.Random(self.seed)
        self.centroids = self._init_kmeans_pp(xs, rng)
        k = len(self.centroids)

        labels = [0] * len(xs)
        for _ in range(self.max_iter):
            new_labels = [
                min(range(k), key=lambda ci: _dist_sq(p, self.centroids[ci]))
                for p in xs
            ]
            if new_labels == labels and self.is_fitted:
                break
            labels = new_labels
            for ci in range(k):
                members = [xs[i] for i, lbl in enumerate(labels) if lbl == ci]
                if members:
                    self.centroids[ci] = [sum(m[j] for m in members) / len(members) for j in range(d)]

        inertia = sum(_dist_sq(xs[i], self.centroids[labels[i]]) for i in range(len(xs)))
        self.is_fitted = True
        self.trained_at = time.time()
        self.training_metrics = {
            "k": k,
            "inertia": round(inertia, 4),
            "silhouette": self._silhouette(xs, labels),
        }
        return self

    def _silhouette(self, xs: list[list[float]], labels: list[int]) -> float:
        unique = set(labels)
        if len(unique) < 2:
            return 0.0
        scores: list[float] = []
        for i, p in enumerate(xs):
            own = [math.sqrt(_dist_sq(p, xs[j])) for j in range(len(xs)) if j != i and labels[j] == labels[i]]
            a = sum(own) / len(own) if own else 0.0
            b_candidates = []
            for c in unique:
                if c == labels[i]:
                    continue
                other = [math.sqrt(_dist_sq(p, xs[j])) for j in range(len(xs)) if labels[j] == c]
                if other:
                    b_candidates.append(sum(other) / len(other))
            b = min(b_candidates) if b_candidates else 0.0
            denom = max(a, b)
            scores.append((b - a) / denom if denom > 1e-12 else 0.0)
        return round(sum(scores) / max(1, len(scores)), 4)

    @timed_predict
    def predict(self, data: list[float] | dict[str, Any]) -> PredictionResult:
        if not self.is_fitted:
            raise RuntimeError("KMeansClusterer must be fitted before predict().")
        features = data["features"] if isinstance(data, dict) else data
        vec = [float(v) for v in features]
        dists = [math.sqrt(_dist_sq(vec, c)) for c in self.centroids]
        best = min(range(len(dists)), key=lambda i: dists[i])
        inv = [1.0 / (d + 1e-6) for d in dists]
        conf = inv[best] / sum(inv)
        return PredictionResult(
            model=self.metadata.key,
            prediction=best,
            confidence=round(conf, 4),
            details={
                "cluster_id": best,
                "distances": [round(d, 4) for d in dists],
                "centroid": [round(v, 4) for v in self.centroids[best]],
            },
        )

    def get_state(self) -> dict[str, Any]:
        return {"k": self.k, "max_iter": self.max_iter, "seed": self.seed, "centroids": self.centroids}

    def set_state(self, state: dict[str, Any]) -> None:
        self.k = int(state["k"])
        self.max_iter = int(state["max_iter"])
        self.seed = int(state["seed"])
        self.centroids = state["centroids"]

    def _run_demo(self, custom_input: Any = None) -> dict[str, Any]:
        X = [
            [10.0, 80.0], [12.0, 85.0], [14.0, 78.0],
            [50.0, 50.0], [53.0, 48.0], [47.0, 52.0],
            [88.0, 15.0], [92.0, 18.0], [85.0, 12.0],
        ]
        self.fit(X)
        res = self.predict(custom_input or self.metadata.input_example)
        return {"training": self.training_metrics, "result": res.to_dict()}
