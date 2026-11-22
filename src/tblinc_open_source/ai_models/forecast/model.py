"""13. HoltWintersForecaster: Double/Triple Exponential Smoothing time-series forecaster."""

from __future__ import annotations

import math
import time
from typing import Any

from ..core import BaseAIModel, ModelMetadata, PredictionResult, register_model, timed_predict


@register_model
class HoltWintersForecaster(BaseAIModel):
    """Additive Holt-Winters exponential smoothing forecaster with 95% confidence bands."""

    metadata = ModelMetadata(
        key="forecast",
        name="Trend Forecaster",
        category="Time Series",
        task="Multi-Step Forecasting",
        description="Level, trend, and optional seasonal exponential smoothing with prediction intervals.",
        input_example={"horizon": 5},
        tags=["time-series", "forecasting", "holt-winters"],
    )

    def __init__(
        self,
        alpha: float = 0.4,
        beta: float = 0.2,
        gamma: float = 0.2,
        season_length: int = 0,
    ) -> None:
        super().__init__()
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.season_length = max(0, season_length)
        self.level: float = 0.0
        self.trend: float = 0.0
        self.seasonals: list[float] = []
        self.residual_std: float = 0.0

    def fit(self, series: list[float]) -> HoltWintersForecaster:
        ys = [float(v) for v in series]
        if len(ys) < 3:
            raise ValueError("Time series must contain at least 3 points.")

        m = self.season_length if self.season_length >= 2 and len(ys) >= 2 * self.season_length else 0
        if m > 0:
            self.level = sum(ys[:m]) / m
            self.trend = sum((ys[m + i] - ys[i]) / m for i in range(m)) / m
            self.seasonals = [ys[i] - self.level for i in range(m)]
        else:
            self.level = ys[0]
            self.trend = ys[1] - ys[0]
            self.seasonals = []

        errors: list[float] = []
        for idx, y in enumerate(ys):
            if m > 0:
                s_idx = idx % m
                pred = self.level + self.trend + self.seasonals[s_idx]
                errors.append(y - pred)
                last_level = self.level
                self.level = self.alpha * (y - self.seasonals[s_idx]) + (1.0 - self.alpha) * (last_level + self.trend)
                self.trend = self.beta * (self.level - last_level) + (1.0 - self.beta) * self.trend
                self.seasonals[s_idx] = self.gamma * (y - self.level) + (1.0 - self.gamma) * self.seasonals[s_idx]
            else:
                pred = self.level + self.trend
                errors.append(y - pred)
                last_level = self.level
                self.level = self.alpha * y + (1.0 - self.alpha) * (last_level + self.trend)
                self.trend = self.beta * (self.level - last_level) + (1.0 - self.beta) * self.trend

        mse = sum(e * e for e in errors) / max(1, len(errors))
        self.residual_std = math.sqrt(mse)
        self.is_fitted = True
        self.trained_at = time.time()
        self.training_metrics = {
            "observations": len(ys),
            "rmse": round(self.residual_std, 4),
            "final_level": round(self.level, 4),
            "final_trend": round(self.trend, 4),
            "season_length": m,
        }
        return self

    @timed_predict
    def predict(self, data: int | dict[str, Any] = 5) -> PredictionResult:
        if not self.is_fitted:
            raise RuntimeError("HoltWintersForecaster must be fitted before predict().")
        horizon = int(data.get("horizon", 5)) if isinstance(data, dict) else int(data)
        horizon = max(1, min(horizon, 120))
        m = len(self.seasonals)
        forecast: list[float] = []
        intervals: list[dict[str, float]] = []
        for step in range(1, horizon + 1):
            seasonal = self.seasonals[(step - 1) % m] if m > 0 else 0.0
            yhat = self.level + step * self.trend + seasonal
            margin = 1.96 * self.residual_std * math.sqrt(step)
            forecast.append(round(yhat, 3))
            intervals.append({"lower": round(yhat - margin, 3), "upper": round(yhat + margin, 3)})

        return PredictionResult(
            model=self.metadata.key,
            prediction=forecast,
            confidence=0.95,
            details={"horizon": horizon, "confidence_95": intervals},
        )

    def get_state(self) -> dict[str, Any]:
        return {
            "alpha": self.alpha,
            "beta": self.beta,
            "gamma": self.gamma,
            "season_length": self.season_length,
            "level": self.level,
            "trend": self.trend,
            "seasonals": self.seasonals,
            "residual_std": self.residual_std,
        }

    def set_state(self, state: dict[str, Any]) -> None:
        self.alpha = float(state["alpha"])
        self.beta = float(state["beta"])
        self.gamma = float(state["gamma"])
        self.season_length = int(state["season_length"])
        self.level = float(state["level"])
        self.trend = float(state["trend"])
        self.seasonals = [float(v) for v in state["seasonals"]]
        self.residual_std = float(state["residual_std"])

    def _run_demo(self, custom_input: Any = None) -> dict[str, Any]:
        # Monthly API traffic (thousands) with steady growth + quarterly seasonality
        series = [120, 135, 150, 142, 160, 178, 195, 188, 210, 228, 246, 240]
        self.season_length = 4
        self.fit(series)
        res = self.predict(custom_input or self.metadata.input_example)
        return {"training": self.training_metrics, "result": res.to_dict()}
