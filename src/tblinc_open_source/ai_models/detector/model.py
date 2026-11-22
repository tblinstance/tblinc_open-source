"""12. IsolationForestDetector: Real Isolation Forest anomaly & fraud detector."""

from __future__ import annotations

import math
import random
import time
from typing import Any

from ..core import BaseAIModel, ModelMetadata, PredictionResult, register_model, timed_predict


def _c_factor(n: int) -> float:
    if n <= 1:
        return 0.0
    if n == 2:
        return 1.0
    return 2.0 * (math.log(n - 1) + 0.5772156649) - (2.0 * (n - 1) / n)


@register_model
class IsolationForestDetector(BaseAIModel):
    """Unsupervised Isolation Forest computing normalized path-length anomaly scores."""

    metadata = ModelMetadata(
        key="detector",
        name="Anomaly & Fraud Detector",
        category="Anomaly & Security",
        task="Outlier & Fraud Detection",
        description="Randomly partitions feature space with isolation trees to score anomalous samples.",
        input_example={"features": [9500.0, 142.0, 99.0]},
        tags=["anomaly", "fraud", "isolation-forest", "security"],
    )

    def __init__(self, n_trees: int = 30, sample_size: int = 64, threshold: float = 0.6, seed: int = 42) -> None:
        super().__init__()
        self.n_trees = max(5, n_trees)
        self.sample_size = max(4, sample_size)
        self.threshold = threshold
        self.seed = seed
        self.trees: list[dict[str, Any]] = []
        self.train_n: int = 0

    def _build_itree(self, pts: list[list[float]], depth: int, max_depth: int, rng: random.Random) -> dict[str, Any]:
        if depth >= max_depth or len(pts) <= 1:
            return {"leaf": True, "size": len(pts)}
        d = len(pts[0])
        feat = rng.randrange(d)
        vals = [p[feat] for p in pts]
        lo, hi = min(vals), max(vals)
        if hi - lo <= 1e-12:
            return {"leaf": True, "size": len(pts)}
        split = rng.uniform(lo, hi)
        left = [p for p in pts if p[feat] < split]
        right = [p for p in pts if p[feat] >= split]
        return {
            "leaf": False,
            "feature": feat,
            "split": split,
            "left": self._build_itree(left, depth + 1, max_depth, rng),
            "right": self._build_itree(right, depth + 1, max_depth, rng),
        }

    def _path_len(self, node: dict[str, Any], x: list[float], depth: int = 0) -> float:
        if node["leaf"]:
            return depth + _c_factor(node["size"])
        if x[node["feature"]] < node["split"]:
            return self._path_len(node["left"], x, depth + 1)
        return self._path_len(node["right"], x, depth + 1)

    def fit(self, X: list[list[float]]) -> IsolationForestDetector:
        if len(X) < 3:
            raise ValueError("IsolationForestDetector requires at least 3 samples.")
        xs = [[float(v) for v in row] for row in X]
        rng = random.Random(self.seed)
        sub_n = min(self.sample_size, len(xs))
        max_depth = max(1, int(math.ceil(math.log2(max(2, sub_n)))))
        self.train_n = sub_n
        self.trees = []
        for _ in range(self.n_trees):
            sample = rng.sample(xs, sub_n)
            self.trees.append(self._build_itree(sample, 0, max_depth, rng))
        self.is_fitted = True
        self.trained_at = time.time()
        self.training_metrics = {
            "n_trees": len(self.trees),
            "sample_size": sub_n,
            "threshold": self.threshold,
        }
        return self

    def anomaly_score(self, x: list[float]) -> float:
        avg_h = sum(self._path_len(t, x) for t in self.trees) / len(self.trees)
        c = _c_factor(self.train_n) or 1.0
        return 2.0 ** (-avg_h / c)

    @timed_predict
    def predict(self, data: list[float] | dict[str, Any]) -> PredictionResult:
        if not self.is_fitted:
            raise RuntimeError("IsolationForestDetector must be fitted before predict().")
        features = data["features"] if isinstance(data, dict) else data
        score = self.anomaly_score([float(v) for v in features])
        is_anomaly = score >= self.threshold
        return PredictionResult(
            model=self.metadata.key,
            prediction="anomaly" if is_anomaly else "normal",
            confidence=round(score if is_anomaly else 1.0 - score, 4),
            details={"anomaly_score": round(score, 4), "threshold": self.threshold, "is_anomaly": is_anomaly},
        )

    def get_state(self) -> dict[str, Any]:
        return {
            "n_trees": self.n_trees,
            "sample_size": self.sample_size,
            "threshold": self.threshold,
            "seed": self.seed,
            "train_n": self.train_n,
            "trees": self.trees,
        }

    def set_state(self, state: dict[str, Any]) -> None:
        self.n_trees = int(state["n_trees"])
        self.sample_size = int(state["sample_size"])
        self.threshold = float(state["threshold"])
        self.seed = int(state["seed"])
        self.train_n = int(state["train_n"])
        self.trees = state["trees"]

    def _run_demo(self, custom_input: Any = None) -> dict[str, Any]:
        # Normal telemetry: [tx_amount, latency_ms, req_rate]
        rng = random.Random(7)
        normal = [
            [rng.gauss(120.0, 20.0), rng.gauss(22.0, 4.0), rng.gauss(15.0, 3.0)]
            for _ in range(40)
        ]
        self.fit(normal)
        res = self.predict(custom_input or self.metadata.input_example)
        return {"training": self.training_metrics, "result": res.to_dict()}
