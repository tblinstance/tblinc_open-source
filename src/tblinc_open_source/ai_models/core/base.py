"""Core abstractions and registry for all built-in tblinc AI models."""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass
class ModelMetadata:
    """Descriptive metadata for an AI model exposed to CLI, Web UI, and Admin."""

    key: str
    name: str
    category: str
    task: str
    description: str
    version: str = "1.0.0"
    input_example: Any = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PredictionResult:
    """Structured inference result returned by every tblinc AI model."""

    model: str
    prediction: Any
    confidence: float | None = None
    details: dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BaseAIModel(ABC):
    """Unified interface implemented by all 25 built-in tblinc AI models."""

    metadata: ModelMetadata

    def __init__(self) -> None:
        self.is_fitted: bool = False
        self.trained_at: float | None = None
        self.training_metrics: dict[str, Any] = {}

    @abstractmethod
    def fit(self, *args: Any, **kwargs: Any) -> BaseAIModel:
        """Train or fit the model on input data."""

    @abstractmethod
    def predict(self, data: Any, **kwargs: Any) -> PredictionResult:
        """Run inference and return a structured PredictionResult."""

    def evaluate(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Evaluate model quality; subclasses override with task-specific metrics."""
        return {"fitted": self.is_fitted, **self.training_metrics}

    @abstractmethod
    def get_state(self) -> dict[str, Any]:
        """Return JSON-serializable state dictionary."""

    @abstractmethod
    def set_state(self, state: dict[str, Any]) -> None:
        """Restore model state from a dictionary."""

    def save(self, path: str | Path) -> Path:
        """Persist trained model weights and metadata as JSON."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "key": self.metadata.key,
            "version": self.metadata.version,
            "is_fitted": self.is_fitted,
            "trained_at": self.trained_at,
            "training_metrics": self.training_metrics,
            "state": self.get_state(),
        }
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return target

    @classmethod
    def load(cls, path: str | Path) -> BaseAIModel:
        """Load a previously saved model from JSON."""
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        instance = cls()
        instance.set_state(payload["state"])
        instance.is_fitted = bool(payload.get("is_fitted", True))
        instance.trained_at = payload.get("trained_at")
        instance.training_metrics = payload.get("training_metrics", {})
        return instance

    def demo(self, custom_input: Any = None) -> dict[str, Any]:
        """Run an end-to-end self-contained demo (train + predict) for CLI & Admin Studio."""
        t0 = time.perf_counter()
        result = self._run_demo(custom_input)
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        result.setdefault("elapsed_ms", elapsed_ms)
        result.setdefault("model", self.metadata.to_dict())
        return result

    @abstractmethod
    def _run_demo(self, custom_input: Any = None) -> dict[str, Any]:
        """Model-specific demonstration pipeline."""

    def info(self) -> dict[str, Any]:
        return {
            **self.metadata.to_dict(),
            "is_fitted": self.is_fitted,
            "trained_at": self.trained_at,
            "training_metrics": self.training_metrics,
        }


class ModelRegistry:
    """Central registry for discovering, instantiating, and inspecting AI models."""

    def __init__(self) -> None:
        self._models: dict[str, type[BaseAIModel]] = {}
        self._aliases: dict[str, str] = {}

    def register(self, cls: type[BaseAIModel]) -> type[BaseAIModel]:
        key = cls.metadata.key
        self._models[key] = cls
        return cls

    def register_alias(self, alias: str, target_key: str) -> None:
        self._aliases[alias] = target_key

    def resolve_key(self, key: str) -> str:
        return self._aliases.get(key, key)

    def get(self, key: str) -> type[BaseAIModel]:
        canonical = self.resolve_key(key)
        if canonical not in self._models:
            available = ", ".join(sorted(self._models))
            raise KeyError(f"Unknown AI model '{key}'. Available: {available}")
        return self._models[canonical]

    def create(self, key: str, **kwargs: Any) -> BaseAIModel:
        return self.get(key)(**kwargs)

    def keys(self) -> list[str]:
        return list(self._models.keys())

    def list_metadata(self) -> list[dict[str, Any]]:
        return [cls.metadata.to_dict() for cls in self._models.values()]

    def by_category(self) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for cls in self._models.values():
            grouped.setdefault(cls.metadata.category, []).append(cls.metadata.to_dict())
        return grouped

    def __len__(self) -> int:
        return len(self._models)

    def __contains__(self, key: str) -> bool:
        return self.resolve_key(key) in self._models


registry = ModelRegistry()


def register_model(cls: type[BaseAIModel]) -> type[BaseAIModel]:
    """Class decorator that registers a BaseAIModel subclass globally."""
    return registry.register(cls)


def timed_predict(fn: Callable[..., PredictionResult]) -> Callable[..., PredictionResult]:
    """Attach accurate inference latency_ms to PredictionResult."""

    def wrapper(self: Any, *args: Any, **kwargs: Any) -> PredictionResult:
        t0 = time.perf_counter()
        res = fn(self, *args, **kwargs)
        res.latency_ms = round((time.perf_counter() - t0) * 1000.0, 3)
        return res

    return wrapper
