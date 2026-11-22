"""9. RandomForestEnsemble: Bagged ensemble of CART trees with random feature subspacing."""

from __future__ import annotations

import math
import random
import time
from collections import Counter
from typing import Any

from ..core import BaseAIModel, ModelMetadata, PredictionResult, register_model, timed_predict
from ..tree import DecisionTreeModel


@register_model
class RandomForestEnsemble(BaseAIModel):
    """Bootstrap-aggregated Random Forest classifier with majority vote confidence."""

    metadata = ModelMetadata(
        key="forest",
        name="Random Forest AI",
        category="Tabular / ML",
        task="Ensemble Classification",
        description="Bagged decision tree forest with random feature subsampling and vote probabilities.",
        input_example={"features": [5.1, 3.5, 1.4, 0.2]},
        tags=["ensemble", "random-forest", "bagging", "tabular"],
    )

    def __init__(self, n_estimators: int = 15, max_depth: int = 6, seed: int = 42) -> None:
        super().__init__()
        self.n_estimators = max(3, n_estimators)
        self.max_depth = max_depth
        self.seed = seed
        self.trees: list[DecisionTreeModel] = []
        self.feature_importances: list[float] = []

    def fit(self, X: list[list[float]], y: list[Any]) -> RandomForestEnsemble:
        if not X or len(X) != len(y):
            raise ValueError("X and y must be non-empty and match in length.")
        n = len(X)
        d = len(X[0])
        max_feat = max(1, int(math.sqrt(d)))
        rng = random.Random(self.seed)

        self.trees = []
        agg_imp = [0.0] * d
        for t in range(self.n_estimators):
            idxs = [rng.randrange(n) for _ in range(n)]
            bx = [X[i] for i in idxs]
            by = [y[i] for i in idxs]
            tree = DecisionTreeModel(
                max_depth=self.max_depth,
                max_features=max_feat,
                seed=self.seed + t + 1,
            )
            tree.fit(bx, by)
            self.trees.append(tree)
            for j, val in enumerate(tree.feature_importances):
                agg_imp[j] += val

        tot = sum(agg_imp) or 1.0
        self.feature_importances = [round(v / tot, 4) for v in agg_imp]
        self.is_fitted = True
        self.trained_at = time.time()
        self.training_metrics = {
            **self.evaluate(X, y),
            "n_estimators": len(self.trees),
            "feature_importances": self.feature_importances,
        }
        return self

    @timed_predict
    def predict(self, data: list[float] | dict[str, Any]) -> PredictionResult:
        if not self.is_fitted:
            raise RuntimeError("RandomForestEnsemble must be fitted before predict().")
        features = data["features"] if isinstance(data, dict) else data
        votes = [tree.predict(features).prediction for tree in self.trees]
        counts = Counter(votes)
        winner, cnt = counts.most_common(1)[0]
        probs = {str(k): round(v / len(votes), 4) for k, v in counts.items()}
        return PredictionResult(
            model=self.metadata.key,
            prediction=winner,
            confidence=round(cnt / len(votes), 4),
            details={"vote_distribution": probs, "n_estimators": len(self.trees)},
        )

    def evaluate(self, X: list[list[float]], y: list[Any]) -> dict[str, Any]:
        correct = sum(1 for xi, yi in zip(X, y) if self.predict(xi).prediction == yi)
        return {"accuracy": round(correct / max(1, len(y)), 4), "samples": len(y)}

    def get_state(self) -> dict[str, Any]:
        return {
            "n_estimators": self.n_estimators,
            "max_depth": self.max_depth,
            "seed": self.seed,
            "feature_importances": self.feature_importances,
            "trees": [t.get_state() for t in self.trees],
        }

    def set_state(self, state: dict[str, Any]) -> None:
        self.n_estimators = int(state["n_estimators"])
        self.max_depth = int(state["max_depth"])
        self.seed = int(state["seed"])
        self.feature_importances = list(state["feature_importances"])
        self.trees = []
        for ts in state["trees"]:
            tree = DecisionTreeModel()
            tree.set_state(ts)
            tree.is_fitted = True
            self.trees.append(tree)

    def _run_demo(self, custom_input: Any = None) -> dict[str, Any]:
        # Classic Iris-style botanical features
        X = [
            [5.1, 3.5, 1.4, 0.2], [4.9, 3.0, 1.4, 0.2], [5.4, 3.9, 1.7, 0.4],
            [7.0, 3.2, 4.7, 1.4], [6.4, 3.2, 4.5, 1.5], [6.9, 3.1, 4.9, 1.5],
            [6.3, 3.3, 6.0, 2.5], [7.1, 3.0, 5.9, 2.1], [6.5, 3.0, 5.8, 2.2],
        ]
        y = [
            "setosa", "setosa", "setosa",
            "versicolor", "versicolor", "versicolor",
            "virginica", "virginica", "virginica",
        ]
        self.fit(X, y)
        res = self.predict(custom_input or self.metadata.input_example)
        return {"training": self.training_metrics, "result": res.to_dict()}
