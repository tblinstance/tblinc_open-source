"""7. LogisticClassifier: L2-regularized multinomial softmax logistic regression."""

from __future__ import annotations

import math
import time
from typing import Any

from ..core import BaseAIModel, ModelMetadata, PredictionResult, register_model, timed_predict


@register_model
class LogisticClassifier(BaseAIModel):
    """Feature-standardized L2 multinomial logistic regression with gradient descent."""

    metadata = ModelMetadata(
        key="classify",
        name="Smart Category Classifier",
        category="Tabular / ML",
        task="Binary & Multi-class Classification",
        description="Standardized L2-regularized softmax logistic regression with calibrated class probabilities.",
        input_example={"features": [720, 85000, 0.22]},
        tags=["tabular", "classification", "logistic", "linear"],
    )

    def __init__(self, lr: float = 0.2, l2: float = 0.01, epochs: int = 200) -> None:
        super().__init__()
        self.lr = lr
        self.l2 = l2
        self.epochs = epochs
        self.classes: list[Any] = []
        self.means: list[float] = []
        self.stds: list[float] = []
        self.weights: list[list[float]] = []
        self.biases: list[float] = []

    def _standardize(self, row: list[float]) -> list[float]:
        return [(float(v) - m) / s for v, m, s in zip(row, self.means, self.stds)]

    def _softmax(self, logits: list[float]) -> list[float]:
        mx = max(logits)
        exps = [math.exp(v - mx) for v in logits]
        s = sum(exps) or 1.0
        return [e / s for e in exps]

    def fit(self, X: list[list[float]], y: list[Any]) -> LogisticClassifier:
        if not X or len(X) != len(y):
            raise ValueError("X and y must be non-empty and match in length.")
        n = len(X)
        d = len(X[0])
        self.means = [sum(float(r[j]) for r in X) / n for j in range(d)]
        self.stds = [
            max(1e-8, math.sqrt(sum((float(r[j]) - self.means[j]) ** 2 for r in X) / n))
            for j in range(d)
        ]
        xs = [self._standardize(r) for r in X]
        self.classes = sorted(set(y), key=lambda v: str(v))
        c2i = {c: i for i, c in enumerate(self.classes)}
        k = len(self.classes)
        self.weights = [[0.0] * d for _ in range(k)]
        self.biases = [0.0] * k

        for _ in range(self.epochs):
            gw = [[0.0] * d for _ in range(k)]
            gb = [0.0] * k
            for xi, yi in zip(xs, y):
                logits = [sum(w * v for w, v in zip(self.weights[c], xi)) + self.biases[c] for c in range(k)]
                probs = self._softmax(logits)
                t = c2i[yi]
                for c in range(k):
                    err = probs[c] - (1.0 if c == t else 0.0)
                    gb[c] += err
                    for j in range(d):
                        gw[c][j] += err * xi[j]
            for c in range(k):
                self.biases[c] -= self.lr * (gb[c] / n)
                for j in range(d):
                    self.weights[c][j] -= self.lr * ((gw[c][j] / n) + self.l2 * self.weights[c][j])

        self.is_fitted = True
        self.trained_at = time.time()
        self.training_metrics = self.evaluate(X, y)
        return self

    @timed_predict
    def predict(self, data: list[float] | dict[str, Any]) -> PredictionResult:
        if not self.is_fitted:
            raise RuntimeError("LogisticClassifier must be fitted before predict().")
        features = data["features"] if isinstance(data, dict) else data
        xi = self._standardize([float(v) for v in features])
        logits = [
            sum(w * v for w, v in zip(self.weights[c], xi)) + self.biases[c]
            for c in range(len(self.classes))
        ]
        probs = self._softmax(logits)
        best = max(range(len(probs)), key=lambda i: probs[i])
        return PredictionResult(
            model=self.metadata.key,
            prediction=self.classes[best],
            confidence=round(probs[best], 4),
            details={"probabilities": {str(c): round(p, 4) for c, p in zip(self.classes, probs)}},
        )

    def evaluate(self, X: list[list[float]], y: list[Any]) -> dict[str, Any]:
        correct = sum(1 for xi, yi in zip(X, y) if self.predict(xi).prediction == yi)
        return {"accuracy": round(correct / max(1, len(y)), 4), "samples": len(y)}

    def get_state(self) -> dict[str, Any]:
        return {
            "lr": self.lr,
            "l2": self.l2,
            "epochs": self.epochs,
            "classes": self.classes,
            "means": self.means,
            "stds": self.stds,
            "weights": self.weights,
            "biases": self.biases,
        }

    def set_state(self, state: dict[str, Any]) -> None:
        self.lr = float(state["lr"])
        self.l2 = float(state["l2"])
        self.epochs = int(state["epochs"])
        self.classes = list(state["classes"])
        self.means = list(state["means"])
        self.stds = list(state["stds"])
        self.weights = state["weights"]
        self.biases = list(state["biases"])

    def _run_demo(self, custom_input: Any = None) -> dict[str, Any]:
        # Credit approval: [credit_score, income, debt_ratio]
        X = [
            [760, 95000, 0.15],
            [710, 82000, 0.25],
            [690, 75000, 0.28],
            [540, 32000, 0.65],
            [580, 41000, 0.58],
            [510, 29000, 0.72],
        ]
        y = ["approved", "approved", "approved", "declined", "declined", "declined"]
        self.fit(X, y)
        res = self.predict(custom_input or self.metadata.input_example)
        return {"training": self.training_metrics, "result": res.to_dict()}
