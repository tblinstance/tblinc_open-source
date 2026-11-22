"""8. DecisionTreeModel: CART Gini decision tree classifier with rule inspection."""

from __future__ import annotations

import random
import time
from collections import Counter
from typing import Any

from ..core import BaseAIModel, ModelMetadata, PredictionResult, register_model, timed_predict


def _gini(labels: list[Any]) -> float:
    n = len(labels)
    if n == 0:
        return 0.0
    counts = Counter(labels)
    return 1.0 - sum((c / n) ** 2 for c in counts.values())


@register_model
class DecisionTreeModel(BaseAIModel):
    """CART Decision Tree Classifier with Gini impurity splitting and feature importances."""

    metadata = ModelMetadata(
        key="tree",
        name="Decision Tree AI",
        category="Tabular / ML",
        task="Interpretable Tree Classification",
        description="Gini-impurity CART decision tree with max depth control and feature importance tracking.",
        input_example={"features": [32, 0.8, 12]},
        tags=["tree", "cart", "interpretable", "tabular"],
    )

    def __init__(
        self,
        max_depth: int = 6,
        min_samples_split: int = 2,
        max_features: int | None = None,
        seed: int = 42,
    ) -> None:
        super().__init__()
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.max_features = max_features
        self.seed = seed
        self.tree: dict[str, Any] = {}
        self.n_features: int = 0
        self.feature_importances: list[float] = []

    def _build(
        self,
        X: list[list[float]],
        y: list[Any],
        depth: int,
        rng: random.Random,
        imp: list[float],
    ) -> dict[str, Any]:
        counts = Counter(y)
        majority, maj_cnt = counts.most_common(1)[0]
        leaf = {
            "leaf": True,
            "label": majority,
            "confidence": round(maj_cnt / len(y), 4),
            "counts": {str(k): v for k, v in counts.items()},
        }
        if depth >= self.max_depth or len(y) < self.min_samples_split or len(counts) == 1:
            return leaf

        parent_gini = _gini(y)
        feat_indices = list(range(self.n_features))
        if self.max_features is not None and self.max_features < self.n_features:
            feat_indices = rng.sample(feat_indices, self.max_features)

        best_gain = 0.0
        best_feat = -1
        best_thresh = 0.0
        best_split: tuple[list[int], list[int]] | None = None

        n = len(y)
        for fi in feat_indices:
            vals = sorted({row[fi] for row in X})
            if len(vals) < 2:
                continue
            thresholds = [(vals[i] + vals[i + 1]) / 2.0 for i in range(len(vals) - 1)]
            for thresh in thresholds:
                left_idx = [i for i, row in enumerate(X) if row[fi] <= thresh]
                right_idx = [i for i, row in enumerate(X) if row[fi] > thresh]
                if not left_idx or not right_idx:
                    continue
                g_left = _gini([y[i] for i in left_idx])
                g_right = _gini([y[i] for i in right_idx])
                weighted = (len(left_idx) / n) * g_left + (len(right_idx) / n) * g_right
                gain = parent_gini - weighted
                if gain > best_gain:
                    best_gain = gain
                    best_feat = fi
                    best_thresh = thresh
                    best_split = (left_idx, right_idx)

        if best_split is None or best_gain <= 1e-9:
            return leaf

        imp[best_feat] += best_gain * n
        l_idx, r_idx = best_split
        return {
            "leaf": False,
            "feature": best_feat,
            "threshold": best_thresh,
            "left": self._build([X[i] for i in l_idx], [y[i] for i in l_idx], depth + 1, rng, imp),
            "right": self._build([X[i] for i in r_idx], [y[i] for i in r_idx], depth + 1, rng, imp),
        }

    def fit(self, X: list[list[float]], y: list[Any]) -> DecisionTreeModel:
        if not X or len(X) != len(y):
            raise ValueError("X and y must be non-empty and match in length.")
        self.n_features = len(X[0])
        xs = [[float(v) for v in row] for row in X]
        imp = [0.0] * self.n_features
        rng = random.Random(self.seed)
        self.tree = self._build(xs, list(y), 0, rng, imp)
        total_imp = sum(imp) or 1.0
        self.feature_importances = [round(v / total_imp, 4) for v in imp]
        self.is_fitted = True
        self.trained_at = time.time()
        self.training_metrics = {
            **self.evaluate(xs, y),
            "feature_importances": self.feature_importances,
        }
        return self

    def _traverse(self, node: dict[str, Any], row: list[float]) -> dict[str, Any]:
        while not node["leaf"]:
            if row[node["feature"]] <= node["threshold"]:
                node = node["left"]
            else:
                node = node["right"]
        return node

    @timed_predict
    def predict(self, data: list[float] | dict[str, Any]) -> PredictionResult:
        if not self.is_fitted:
            raise RuntimeError("DecisionTreeModel must be fitted before predict().")
        features = data["features"] if isinstance(data, dict) else data
        leaf = self._traverse(self.tree, [float(v) for v in features])
        return PredictionResult(
            model=self.metadata.key,
            prediction=leaf["label"],
            confidence=leaf["confidence"],
            details={"leaf_counts": leaf["counts"], "feature_importances": self.feature_importances},
        )

    def evaluate(self, X: list[list[float]], y: list[Any]) -> dict[str, Any]:
        correct = sum(1 for xi, yi in zip(X, y) if self.predict(xi).prediction == yi)
        return {"accuracy": round(correct / max(1, len(y)), 4), "samples": len(y)}

    def get_state(self) -> dict[str, Any]:
        return {
            "max_depth": self.max_depth,
            "min_samples_split": self.min_samples_split,
            "max_features": self.max_features,
            "seed": self.seed,
            "n_features": self.n_features,
            "feature_importances": self.feature_importances,
            "tree": self.tree,
        }

    def set_state(self, state: dict[str, Any]) -> None:
        self.max_depth = int(state["max_depth"])
        self.min_samples_split = int(state["min_samples_split"])
        self.max_features = state["max_features"]
        self.seed = int(state["seed"])
        self.n_features = int(state["n_features"])
        self.feature_importances = list(state["feature_importances"])
        self.tree = state["tree"]

    def _run_demo(self, custom_input: Any = None) -> dict[str, Any]:
        # Server health: [cpu_temp_c, load_avg, latency_ms]
        X = [
            [30, 0.5, 10],
            [35, 0.9, 15],
            [42, 1.2, 22],
            [68, 3.8, 95],
            [74, 4.5, 130],
            [88, 7.5, 310],
            [92, 8.9, 420],
        ]
        y = ["healthy", "healthy", "healthy", "degraded", "degraded", "critical", "critical"]
        self.fit(X, y)
        res = self.predict(custom_input or self.metadata.input_example)
        return {"training": self.training_metrics, "result": res.to_dict()}
