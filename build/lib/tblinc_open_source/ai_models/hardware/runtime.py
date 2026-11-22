"""Hardware accelerator & optional ML backend detection (CUDA, Intel XPU, OpenVINO, CPU)."""

from __future__ import annotations

import importlib.util
import os
import platform
from typing import Any


def _is_installed(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ModuleNotFoundError, ValueError):
        return False


def installed_backends() -> dict[str, bool]:
    """Check which optional AI/ML frameworks from pyproject.toml are installed."""
    candidates = [
        "torch",
        "torchvision",
        "torchaudio",
        "safetensors",
        "onnx",
        "tensorflow",
        "keras",
        "jax",
        "transformers",
        "diffusers",
        "accelerate",
        "peft",
        "trl",
        "datasets",
        "tokenizers",
        "huggingface_hub",
        "sentencepiece",
        "sentence_transformers",
        "ultralytics",
        "timm",
        "cv2",
        "PIL",
        "librosa",
        "soundfile",
        "faster_whisper",
        "TTS",
        "numpy",
        "scipy",
        "pandas",
        "sklearn",
        "xgboost",
        "lightgbm",
        "catboost",
        "langchain",
        "llama_index",
        "chromadb",
        "faiss",
        "qdrant_client",
        "tiktoken",
        "openai",
        "anthropic",
        "google.genai",
        "litellm",
        "bitsandbytes",
        "onnxruntime",
        "optimum.intel",
        "openvino",
    ]
    return {name: _is_installed(name) for name in candidates}


def detect_hardware() -> dict[str, Any]:
    """Detect available compute accelerators (CUDA, Intel XPU, MPS, OpenVINO, CPU)."""
    cuda_available = False
    cuda_devices: list[str] = []
    xpu_available = False
    xpu_devices: list[str] = []
    mps_available = False
    openvino_devices: list[str] = []

    if _is_installed("torch"):
        try:
            import torch  # type: ignore[import-not-found]

            if hasattr(torch, "cuda") and torch.cuda.is_available():
                cuda_available = True
                cuda_devices = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
            if hasattr(torch, "xpu") and torch.xpu.is_available():
                xpu_available = True
                xpu_devices = [torch.xpu.get_device_name(i) for i in range(torch.xpu.device_count())]
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                mps_available = True
        except Exception:
            pass

    if _is_installed("openvino"):
        try:
            import openvino as ov  # type: ignore[import-not-found]

            openvino_devices = list(ov.Core().available_devices)
        except Exception:
            pass

    preferred = "cuda" if cuda_available else ("xpu" if xpu_available else ("mps" if mps_available else "cpu"))
    return {
        "preferred_device": preferred,
        "cpu_cores": os.cpu_count() or 1,
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cuda": {"available": cuda_available, "devices": cuda_devices},
        "xpu": {"available": xpu_available, "devices": xpu_devices},
        "mps": {"available": mps_available},
        "openvino": {"available": bool(openvino_devices), "devices": openvino_devices},
    }


def select_device(prefer: str = "auto") -> str:
    """Return the best matching device string ('cuda', 'xpu', 'mps', or 'cpu')."""
    hw = detect_hardware()
    if prefer == "auto":
        return str(hw["preferred_device"])
    if prefer == "cuda" and hw["cuda"]["available"]:
        return "cuda"
    if prefer == "xpu" and hw["xpu"]["available"]:
        return "xpu"
    if prefer == "mps" and hw["mps"]["available"]:
        return "mps"
    return "cpu"


def system_report() -> dict[str, Any]:
    """Combined hardware and optional ML stack readiness report."""
    backends = installed_backends()
    return {
        "hardware": detect_hardware(),
        "installed_backends": [name for name, ok in backends.items() if ok],
        "optional_backends": backends,
    }
