"""22. GradientBoostModel: Pure-Python stagewise Gradient Boosted Decision Stumps (XGBoost-style)."""

from __future__ import annotations

import math
import time
from typing import Any

from ..core import BaseAIModel, ModelMetadata, PredictionResult, register_model, timed_predict


@register_model
class GradientBoostModel(BaseAIModel):
    """Additive gradient boosting over decision stumps for high-accuracy tabular prediction."""

    metadata = ModelMetadata(
        key="boost",
        name="Gradient Boosting AI",
        category="Tabular / ML",
        task="Gradient-Boosted Tabular Regression",
        description="Stagewise gradient-boosted decision stumps minimizing squared-error residuals with shrinkage.",
        input_example={"features": [6.0, 2.5, 4.0]},
        tags=["gradient-boosting", "xgboost", "tabular", "regression"],
    )

    def __init__(self, n_estimators: int = 35, learning_rate: float = 0.15) -> None:
        super().__init__()
        self.n_estimators = max(5, n_estimators)
        self.learning_rate = max(0.01, min(1.0, learning_rate))
        self.base_score: float = 0.0
        self.stumps: list[dict[str, Any]] = []

    def _fit_stump(self, X: list[list[float]], residuals: list[float]) -> dict[str, Any]:
        n = len(X)
        d = len(X[0])
        best = {"feature": 0, "threshold": 0.0, "left_val": 0.0, "right_val": 0.0, "loss": float("inf")}
        for f in range(d):
            vals = sorted({row[f] for row in X})
            thresholds = [(vals[i] + vals[i + 1]) / 2.0 for i in range(len(vals) - 1)] or vals
            for thr in thresholds:
                left = [residuals[i] for i in range(n) if X[i][f] <= thr]
                right = [residuals[i] for i in range(n) if X[i][f] > thr]
                if not left or not right:
                    continue
                l_mean = sum(left) / len(left)
                r_mean = sum(right) / len(right)
                loss = sum((v - l_mean) ** 2 for v in left) + sum((v - r_mean) ** 2 for v in right)
                if loss < best["loss"]:
                    best = {
                        "feature": f,
                        "threshold": thr,
                        "left_val": l_mean,
                        "right_val": r_mean,
                        "loss": loss,
                    }
        return best

    def _predict_row(self, row: list[float]) -> float:
        pred = self.base_score
        for s in self.stumps:
            val = s["left_val"] if row[s["feature"]] <= s["threshold"] else s["right_val"]
            pred += self.learning_rate * val
        return pred

    def fit(self, X: list[list[float]], y: list[float]) -> GradientBoostModel:
        if not X or len(X) != len(y):
            raise ValueError("X and y must be non-empty and match in length.")
        xf = [[float(v) for v in row] for row in X]
        yf = [float(v) for v in y]
        self.base_score = sum(yf) / len(yf)
        preds = [self.base_score] * len(yf)
        self.stumps = []

        for _ in range(self.n_estimators):
            residuals = [target - p for target, p in zip(yf, preds)]
            stump = self._fit_stump(xf, residuals)
            if stump["loss"] == float("inf"):
                break
            self.stumps.append(
                {
                    "feature": stump["feature"],
                    "threshold": round(stump["threshold"], 6),
                    "left_val": round(stump["left_val"], 6),
                    "right_val": round(stump["right_val"], 6),
                }
            )
            for i, row in enumerate(xf):
                step = stump["left_val"] if row[stump["feature"]] <= stump["threshold"] else stump["right_val"]
                preds[i] += self.learning_rate * step

        mse = sum((target - p) ** 2 for target, p in zip(yf, preds)) / len(yf)
        var = sum((target - self.base_score) ** 2 for target in yf) / len(yf)
        r2 = 1.0 - (mse / var) if var > 1e-12 else 1.0
        self.is_fitted = True
        self.trained_at = time.time()
        self.training_metrics = {
            "n_estimators": len(self.stumps),
            "learning_rate": self.learning_rate,
            "train_rmse": round(math.sqrt(mse), 4),
            "train_r2": round(r2, 4),
        }
        return self

    @timed_predict
    def predict(self, data: list[float] | dict[str, Any]) -> PredictionResult:
        if not self.is_fitted:
            raise RuntimeError("GradientBoostModel must be fitted before predict().")
        feats = [float(v) for v in (data["features"] if isinstance(data, dict) else data)]
        y_hat = self._predict_row(feats)
        r2 = float(self.training_metrics.get("train_r2", 0.9))
        return PredictionResult(
            model=self.metadata.key,
            prediction=round(y_hat, 4),
            confidence=round(max(0.0, min(1.0, r2)), 4),
            details={"base_score": round(self.base_score, 4), "trees_used": len(self.stumps)},
        )

    def get_state(self) -> dict[str, Any]:
        return {
            "n_estimators": self.n_estimators,
            "learning_rate": self.learning_rate,
            "base_score": self.base_score,
            "stumps": self.stumps,
        }

    def set_state(self, state: dict[str, Any]) -> None:
        self.n_estimators = int(state["n_estimators"])
        self.learning_rate = float(state["learning_rate"])
        self.base_score = float(state["base_score"])
        self.stumps = list(state["stumps"])

    def _run_demo(self, custom_input: Any = None) -> dict[str, Any]:
        X = [
            [1.0, 1.0, 1.0],
            [2.0, 1.5, 2.0],
            [3.0, 2.0, 2.5],
            [4.0, 2.0, 3.0],
            [5.0, 2.5, 3.5],
            [7.0, 3.0, 4.5],
            [8.0, 3.5, 5.0],
            [9.0, 4.0, 6.0],
        ]
        y = [15.0, 26.0, 37.0, 48.0, 61.0, 84.0, 96.0, 112.0]
        self.fit(X, y)
        res = self.predict(custom_input or self.metadata.input_example)
        return {"training": self.training_metrics, "result": res.to_dict()}
