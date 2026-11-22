"""Core AI model abstractions, neural tensor/attention engine, and registry."""

from .base import BaseAIModel, ModelMetadata, ModelRegistry, PredictionResult, register_model, registry, timed_predict
from .engine import (
    AdamWOptimizer,
    BPETokenizer,
    MultiHeadSelfAttention,
    Tensor,
    TransformerBlock,
    active_compute_backend,
)

__all__ = [
    "AdamWOptimizer",
    "BPETokenizer",
    "BaseAIModel",
    "ModelMetadata",
    "ModelRegistry",
    "MultiHeadSelfAttention",
    "PredictionResult",
    "Tensor",
    "TransformerBlock",
    "active_compute_backend",
    "register_model",
    "registry",
    "timed_predict",
]
