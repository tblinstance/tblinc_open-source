"""Built-in hub of 25 clean single-word AI model packages + core & hardware runtimes."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from . import (
    audio,
    boost,
    chat,
    classify,
    cluster,
    core,
    detector,
    embed,
    forecast,
    forest,
    hardware,
    image,
    multimodal,
    music,
    neural,
    objects,
    predict,
    recommend,
    search,
    sentiment,
    similarity,
    summarize,
    transcribe,
    tree,
    video,
    vision,
    voice,
)
from .audio import AudioSpectrumModel
from .boost import GradientBoostModel
from .chat import MiniTransformerLM
from .classify import LogisticClassifier
from .cluster import KMeansClusterer
from .core import (
    AdamWOptimizer,
    BPETokenizer,
    BaseAIModel,
    ModelMetadata,
    ModelRegistry,
    MultiHeadSelfAttention,
    PredictionResult,
    Tensor,
    TransformerBlock,
    active_compute_backend,
    register_model,
    registry,
)
from .detector import IsolationForestDetector
from .embed import EmbeddingModel
from .forecast import HoltWintersForecaster
from .forest import RandomForestEnsemble
from .hardware import detect_hardware, installed_backends, select_device, system_report
from .image import MiniDiffusionModel
from .multimodal import MultimodalVLM
from .music import MusicComposerModel
from .neural import MLPNeuralNet
from .objects import ObjectDetectorModel
from .predict import RidgeLinearRegressor
from .recommend import MatrixFactorizationRecommender
from .search import RAGEngine
from .sentiment import NaiveBayesTextClassifier
from .similarity import KNNModel
from .summarize import TextSummarizerModel
from .transcribe import SpeechToTextModel
from .tree import DecisionTreeModel
from .video import VideoMotionModel
from .vision import VisionConvNet
from .voice import FormantTTSSynthesizer

# Register legacy key aliases so previously saved runs or scripts continue working seamlessly
_LEGACY_KEY_ALIASES: dict[str, str] = {
    "cart": "tree",
    "ddpm": "image",
    "kmeans": "cluster",
    "llm": "chat",
    "logistic": "classify",
    "mlp": "neural",
    "neighbors": "similarity",
    "outlier": "detector",
    "rag": "search",
    "recsys": "recommend",
    "ridge": "predict",
    "timeseries": "forecast",
    "tts": "voice",
    "asr": "transcribe",
    "yolo": "objects",
    "xgboost": "boost",
}
for _old_key, _new_key in _LEGACY_KEY_ALIASES.items():
    registry.register_alias(_old_key, _new_key)


def list_models() -> list[dict[str, Any]]:
    """Return metadata dictionaries for all registered built-in AI models."""
    return registry.list_metadata()


def create_model(key: str, **kwargs: Any) -> BaseAIModel:
    """Instantiate a registered AI model by its registry key."""
    return registry.create(key, **kwargs)


def run_demo(key: str, custom_input: Any = None) -> dict[str, Any]:
    """Instantiate and run the end-to-end train + predict demo for any registered AI model."""
    model = registry.create(key)
    return model.demo(custom_input=custom_input)


def verify_all_models() -> dict[str, Any]:
    """Run full train, predict, and save/load round-trip verification across all registered AI models."""
    results: list[dict[str, Any]] = []
    passed = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        for meta in list_models():
            key = meta["key"]
            try:
                model = create_model(key)
                demo_out = model.demo()
                pred_before = demo_out["result"]["prediction"]
                saved = model.save(Path(tmpdir) / f"{key}.json")
                restored = type(model).load(saved)
                pred_after = restored.predict(meta["input_example"]).prediction
                ok = bool(model.is_fitted and restored.is_fitted and pred_before is not None and pred_after is not None)
                if ok:
                    passed += 1
                results.append(
                    {
                        "key": key,
                        "name": meta["name"],
                        "category": meta["category"],
                        "ok": ok,
                        "latency_ms": demo_out["result"].get("latency_ms", 0.0),
                        "confidence": demo_out["result"].get("confidence"),
                    }
                )
            except Exception as exc:
                results.append({"key": key, "name": meta["name"], "category": meta["category"], "ok": False, "error": str(exc)})
    return {
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "all_ok": passed == len(results),
        "results": results,
    }


__all__ = [
    "AdamWOptimizer",
    "AudioSpectrumModel",
    "BPETokenizer",
    "BaseAIModel",
    "DecisionTreeModel",
    "EmbeddingModel",
    "FormantTTSSynthesizer",
    "GradientBoostModel",
    "HoltWintersForecaster",
    "IsolationForestDetector",
    "KMeansClusterer",
    "KNNModel",
    "LogisticClassifier",
    "MLPNeuralNet",
    "MatrixFactorizationRecommender",
    "MiniDiffusionModel",
    "MiniTransformerLM",
    "ModelMetadata",
    "ModelRegistry",
    "MultiHeadSelfAttention",
    "MultimodalVLM",
    "MusicComposerModel",
    "NaiveBayesTextClassifier",
    "ObjectDetectorModel",
    "PredictionResult",
    "RAGEngine",
    "RandomForestEnsemble",
    "RidgeLinearRegressor",
    "SpeechToTextModel",
    "Tensor",
    "TextSummarizerModel",
    "TransformerBlock",
    "VideoMotionModel",
    "VisionConvNet",
    "active_compute_backend",
    "audio",
    "boost",
    "chat",
    "classify",
    "cluster",
    "core",
    "create_model",
    "detect_hardware",
    "detector",
    "embed",
    "forecast",
    "forest",
    "hardware",
    "image",
    "installed_backends",
    "list_models",
    "multimodal",
    "music",
    "neural",
    "objects",
    "predict",
    "recommend",
    "register_model",
    "registry",
    "run_demo",
    "search",
    "select_device",
    "sentiment",
    "similarity",
    "summarize",
    "system_report",
    "transcribe",
    "tree",
    "verify_all_models",
    "video",
    "vision",
    "voice",
]
