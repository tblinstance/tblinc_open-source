"""6. RidgeLinearRegressor: Closed-form L2-regularized linear regression via Gaussian elimination."""

from __future__ import annotations

import math
import time
from typing import Any

from ..core import BaseAIModel, ModelMetadata, PredictionResult, register_model, timed_predict


def _solve_linear_system(a: list[list[float]], b: list[float]) -> list[float]:
    """Solve Ax = b using Gaussian elimination with partial pivoting."""
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(m[r][col]))
        m[col], m[pivot] = m[pivot], m[col]
        diag = m[col][col]
        if abs(diag) < 1e-12:
            m[col][col] = 1e-12
            diag = 1e-12
        for j in range(col, n + 1):
            m[col][j] /= diag
        for r in range(n):
            if r != col:
                factor = m[r][col]
                for j in range(col, n + 1):
                    m[r][j] -= factor * m[col][j]
    return [m[i][n] for i in range(n)]


@register_model
class RidgeLinearRegressor(BaseAIModel):
    """Exact L2 Ridge Linear Regression with R², MAE, and RMSE evaluation."""

    metadata = ModelMetadata(
        key="predict",
        name="Numeric Value Predictor",
        category="Tabular / ML",
        task="Continuous Regression",
        description="Exact L2-regularized linear regression solved via pivoted Gaussian elimination.",
        input_example={"features": [1500, 3, 2]},
        tags=["tabular", "regression", "ridge", "linear"],
    )

    def __init__(self, alpha: float = 0.01) -> None:
        super().__init__()
        self.alpha = alpha
        self.weights: list[float] = []
        self.bias: float = 0.0

    def fit(self, X: list[list[float]], y: list[float]) -> RidgeLinearRegressor:
        if not X or len(X) != len(y):
            raise ValueError("X and y must be non-empty and match in length.")
        d = len(X[0])
        aug = [[1.0, *[float(v) for v in row]] for row in X]
        p = d + 1
        xtx = [[0.0] * p for _ in range(p)]
        xty = [0.0] * p

        for row, yi in zip(aug, y):
            yf = float(yi)
            for i in range(p):
                xty[i] += row[i] * yf
                for j in range(p):
                    xtx[i][j] += row[i] * row[j]

        # Regularize feature weights (skip bias at index 0)
        for i in range(1, p):
            xtx[i][i] += self.alpha

        params = _solve_linear_system(xtx, xty)
        self.bias = params[0]
        self.weights = params[1:]
        self.is_fitted = True
        self.trained_at = time.time()
        self.training_metrics = self.evaluate(X, y)
        return self

    @timed_predict
    def predict(self, data: list[float] | dict[str, Any]) -> PredictionResult:
        if not self.is_fitted:
            raise RuntimeError("RidgeLinearRegressor must be fitted before predict().")
        features = data["features"] if isinstance(data, dict) else data
        vec = [float(v) for v in features]
        pred = self.bias + sum(w * x for w, x in zip(self.weights, vec))
        return PredictionResult(
            model=self.metadata.key,
            prediction=round(pred, 4),
            confidence=self.training_metrics.get("r2"),
            details={"weights": [round(w, 4) for w in self.weights], "bias": round(self.bias, 4)},
        )

    def evaluate(self, X: list[list[float]], y: list[float]) -> dict[str, Any]:
        preds = [self.bias + sum(w * float(v) for w, v in zip(self.weights, row)) for row in X]
        ys = [float(v) for v in y]
        n = max(1, len(ys))
        mae = sum(abs(p - t) for p, t in zip(preds, ys)) / n
        mse = sum((p - t) ** 2 for p, t in zip(preds, ys)) / n
        mean_y = sum(ys) / n
        ss_tot = sum((t - mean_y) ** 2 for t in ys)
        ss_res = sum((p - t) ** 2 for p, t in zip(preds, ys))
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-12 else 1.0
        return {"r2": round(r2, 4), "rmse": round(math.sqrt(mse), 4), "mae": round(mae, 4)}

    def get_state(self) -> dict[str, Any]:
        return {"alpha": self.alpha, "weights": self.weights, "bias": self.bias}

    def set_state(self, state: dict[str, Any]) -> None:
        self.alpha = float(state["alpha"])
        self.weights = [float(w) for w in state["weights"]]
        self.bias = float(state["bias"])

    def _run_demo(self, custom_input: Any = None) -> dict[str, Any]:
        # House price prediction: [sqft, bedrooms, bathrooms] -> price ($k)
        X = [
            [1000, 2, 1],
            [1200, 2, 2],
            [1600, 3, 2],
            [2000, 4, 3],
            [2400, 4, 3],
            [2800, 5, 4],
        ]
        y = [210.0, 255.0, 330.0, 425.0, 495.0, 585.0]
        self.fit(X, y)
        res = self.predict(custom_input or self.metadata.input_example)
        return {"training": self.training_metrics, "result": res.to_dict()}
