"""Admin Model Training Engine, TrainingRun ORM model, and sample dataset presets for all 25 AI models."""

from __future__ import annotations

import inspect
import time
from pathlib import Path
from typing import Any

from ...ai_models import create_model, list_models, registry, select_device
from ..orm import CharField, DateTimeField, FloatField, JSONField, Model


_MODEL_KEY_CHOICES = [(m["key"], f"{m['name']} ({m['key']})") for m in list_models()]
_DEVICE_CHOICES = [("cpu", "CPU"), ("cuda", "NVIDIA CUDA"), ("xpu", "Intel XPU"), ("mps", "Apple MPS")]
_STATUS_CHOICES = [("completed", "Completed"), ("queued", "Queued"), ("running", "Running"), ("failed", "Failed")]


class TrainingRun(Model):
    """Persisted record of every AI model training job executed from the Admin Panel."""

    run_name = CharField(max_length=160)
    model_key = CharField(
        max_length=64,
        choices=_MODEL_KEY_CHOICES,
        default="sentiment",
        verbose_name="AI Model",
        help_text="Select one of the 25 built-in AI models.",
    )
    device = CharField(max_length=32, choices=_DEVICE_CHOICES, default="cpu")
    status = CharField(max_length=32, choices=_STATUS_CHOICES, default="completed")
    hyperparams = JSONField(default=dict)
    metrics = JSONField(default=dict)
    artifact_path = CharField(max_length=255, blank=True, default="")
    duration_ms = FloatField(default=0.0)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        table_name = "tblinc_training_runs"
        verbose_name = "Job"
        verbose_name_plural = "Jobs"


# Curated starter training datasets & hyperparams so admins can edit & train any model immediately
TRAINING_PRESETS: dict[str, dict[str, Any]] = {
    "sentiment": {
        "hyperparams": {"alpha": 1.0},
        "dataset": {
            "texts": [
                "Love this AI toolkit, blazing fast and clean!",
                "Awesome admin training workflow and zero bloat.",
                "Great accuracy and simple pip install.",
                "Terrible crash and slow broken pipeline.",
                "Worst bug, frustrating failures everywhere.",
                "Bad documentation and poor performance.",
            ],
            "labels": ["positive", "positive", "positive", "negative", "negative", "negative"],
        },
        "test_input": {"text": "This training studio is awesome and super fast!"},
    },
    "chat": {
        "hyperparams": {"context_window": 4, "embed_dim": 16, "epochs": 5, "lr": 0.08},
        "dataset": {
            "corpus": [
                "tblinc trains custom ai models directly inside the admin panel.",
                "developers build fast modular ai web apps using pure python.",
                "tblinc supports chat images video audio music and custom training.",
            ]
        },
        "test_input": {"prompt": "tblinc trains", "max_tokens": 12, "temperature": 0.7},
    },
    "search": {
        "hyperparams": {"chunk_size": 240},
        "dataset": {
            "documents": [
                {"source": "training.md", "text": "The tblinc Admin Training Center lets staff train all 25 AI models on custom datasets and save weights to disk."},
                {"source": "web.md", "text": "tblinc provides a standalone MTV and MVC Python web framework with SQLite ORM, forms, auth, and Light/Dark UI."},
            ]
        },
        "test_input": {"query": "How do I train custom models in admin?", "top_k": 2},
    },
    "neural": {
        "hyperparams": {"hidden_sizes": [10, 6], "lr": 0.03, "epochs": 80},
        "dataset": {
            "X": [[0.9, 0.85, 0.1], [0.85, 0.9, 0.15], [0.1, 0.2, 0.9], [0.15, 0.1, 0.85]],
            "y": ["gpu_heavy", "gpu_heavy", "edge_tiny", "edge_tiny"],
        },
        "test_input": {"features": [0.88, 0.82, 0.12]},
    },
    "predict": {
        "hyperparams": {"alpha": 0.01},
        "dataset": {
            "X": [[1000, 2], [1400, 3], [1800, 3], [2200, 4], [2600, 5]],
            "y": [200.0, 285.0, 360.0, 445.0, 530.0],
        },
        "test_input": {"features": [1600, 3]},
    },
    "classify": {
        "hyperparams": {"lr": 0.2, "l2": 0.01, "epochs": 150},
        "dataset": {
            "X": [[760, 90000, 0.18], [710, 80000, 0.24], [520, 30000, 0.68], [560, 38000, 0.61]],
            "y": ["approved", "approved", "declined", "declined"],
        },
        "test_input": {"features": [730, 85000, 0.2]},
    },
    "tree": {
        "hyperparams": {"max_depth": 5, "min_samples_split": 2},
        "dataset": {
            "X": [[30, 0.6, 12], [38, 1.0, 18], [72, 4.2, 110], [90, 8.5, 380]],
            "y": ["healthy", "healthy", "degraded", "critical"],
        },
        "test_input": {"features": [34, 0.8, 14]},
    },
    "forest": {
        "hyperparams": {"n_estimators": 15, "max_depth": 5},
        "dataset": {
            "X": [
                [5.1, 3.5, 1.4, 0.2], [4.9, 3.0, 1.4, 0.2],
                [7.0, 3.2, 4.7, 1.4], [6.4, 3.2, 4.5, 1.5],
                [6.3, 3.3, 6.0, 2.5], [7.1, 3.0, 5.9, 2.1],
            ],
            "y": ["setosa", "setosa", "versicolor", "versicolor", "virginica", "virginica"],
        },
        "test_input": {"features": [5.0, 3.4, 1.5, 0.2]},
    },
    "cluster": {
        "hyperparams": {"k": 3, "max_iter": 40},
        "dataset": {
            "X": [[10, 80], [12, 84], [50, 50], [52, 48], [88, 15], [91, 17]],
        },
        "test_input": {"features": [11, 82]},
    },
    "similarity": {
        "hyperparams": {"k": 3, "metric": "euclidean"},
        "dataset": {
            "X": [[1.0, 1.2], [1.9, 2.0], [8.0, 7.6], [8.5, 8.1]],
            "y": ["cluster_a", "cluster_a", "cluster_b", "cluster_b"],
        },
        "test_input": {"features": [1.5, 1.6]},
    },
    "detector": {
        "hyperparams": {"n_trees": 30, "threshold": 0.6},
        "dataset": {
            "X": [[100, 20, 12], [115, 22, 14], [108, 19, 13], [122, 24, 15], [98, 21, 11], [112, 23, 14]],
        },
        "test_input": {"features": [9500, 180, 95]},
    },
    "forecast": {
        "hyperparams": {"alpha": 0.4, "beta": 0.2, "gamma": 0.2, "season_length": 4},
        "dataset": {
            "series": [100, 115, 130, 122, 140, 158, 175, 168, 190, 210, 228, 220],
        },
        "test_input": {"horizon": 4},
    },
    "recommend": {
        "hyperparams": {"n_factors": 6, "lr": 0.03, "epochs": 100},
        "dataset": {
            "interactions": [
                ["alice", "llm_kit", 5.0], ["alice", "rag_studio", 4.8], ["alice", "vision_pro", 2.0],
                ["bob", "llm_kit", 4.9], ["bob", "rag_studio", 4.7], ["bob", "music_ai", 5.0],
                ["carol", "vision_pro", 5.0], ["carol", "video_ai", 4.9],
            ]
        },
        "test_input": {"user": "alice", "top_k": 2},
    },
    "voice": {
        "hyperparams": {"sample_rate": 8000, "base_pitch_hz": 165.0},
        "dataset": {
            "voice_profiles": {
                "studio": {"pitch_hz": 175.0, "brightness": 0.7},
                "deep": {"pitch_hz": 120.0, "brightness": 0.4},
            }
        },
        "test_input": {"text": "Custom trained voice ready", "voice": "studio"},
    },
    "music": {
        "hyperparams": {"sample_rate": 16000},
        "dataset": {},
        "test_input": {"mood": "synthwave", "bpm": 118, "duration_sec": 3.0},
    },
    "image": {
        "hyperparams": {"timesteps": 16, "beta_start": 0.02, "beta_end": 0.25, "seed": 42},
        "dataset": {
            "samples": {
                "star": [
                    [
                        [0, 0, 1, 0, 0],
                        [0, 1, 1, 1, 0],
                        [1, 1, 1, 1, 1],
                        [0, 1, 1, 1, 0],
                        [0, 0, 1, 0, 0],
                    ]
                ],
                "heart": [
                    [
                        [0, 1, 0, 1, 0],
                        [1, 1, 1, 1, 1],
                        [1, 1, 1, 1, 1],
                        [0, 1, 1, 1, 0],
                        [0, 0, 1, 0, 0],
                    ]
                ],
                "ring": [
                    [
                        [0, 1, 1, 1, 0],
                        [1, 0, 0, 0, 1],
                        [1, 0, 0, 0, 1],
                        [1, 0, 0, 0, 1],
                        [0, 1, 1, 1, 0],
                    ]
                ],
            }
        },
        "test_input": {"prompt": "heart", "style": "neon", "steps": 12, "guidance": 1.5, "seed": 7},
    },
    "vision": {
        "hyperparams": {"lr": 0.15, "epochs": 120},
        "dataset": {
            "images": [
                [[0, 0, 1, 0, 0], [0, 0, 1, 0, 0], [1, 1, 1, 1, 1], [0, 0, 1, 0, 0], [0, 0, 1, 0, 0]],
                [[1, 1, 1, 1, 1], [1, 0, 0, 0, 1], [1, 0, 0, 0, 1], [1, 0, 0, 0, 1], [1, 1, 1, 1, 1]],
                [[1, 0, 0, 0, 0], [0, 1, 0, 0, 0], [0, 0, 1, 0, 0], [0, 0, 0, 1, 0], [0, 0, 0, 0, 1]],
            ],
            "labels": ["plus", "square", "diagonal"],
        },
        "test_input": {
            "image": [[1, 1, 1, 1, 1], [1, 0, 0, 0, 1], [1, 0, 0, 0, 1], [1, 0, 0, 0, 1], [1, 1, 1, 1, 1]]
        },
    },
    "embed": {
        "hyperparams": {"dim": 32},
        "dataset": {
            "texts": [
                "tblinc pure python AI framework with built-in ORM and admin panel.",
                "Manage API keys, token quotas, and live usage analytics for all 25 models.",
                "Generate diffusion images, animated videos, spoken voice, and polyphonic music.",
            ]
        },
        "test_input": {"text": "token quota api keys admin", "top_k": 2},
    },
    "boost": {
        "hyperparams": {"n_estimators": 35, "learning_rate": 0.15},
        "dataset": {
            "X": [[1, 1, 1], [2, 1.5, 2], [4, 2, 3], [6, 2.5, 4], [8, 3.5, 5], [9, 4, 6]],
            "y": [15.0, 26.0, 48.0, 72.0, 96.0, 112.0],
        },
        "test_input": {"features": [5.0, 2.5, 3.5]},
    },
    "summarize": {
        "hyperparams": {},
        "dataset": {
            "documents": [
                "tblinc offers 25 built-in AI models and a standalone MTV/MVC web framework.",
                "Admins can control per-model token quotas, issue API keys, and train models.",
            ]
        },
        "test_input": {
            "text": "tblinc is a pure Python AI platform with 25 built-in models. It includes an auto-generated Admin Panel with API keys and token quotas. Developers can launch apps immediately with tblinc serve.",
            "max_sentences": 2,
        },
    },
    "objects": {
        "hyperparams": {"threshold": 0.45, "iou_threshold": 0.5},
        "dataset": {
            "prototypes": {
                "square_box": [4.0, 1.0, 1.0, 1.0],
                "vertical_bar": [3.0, 0.33, 1.0, 1.0],
                "horizontal_bar": [4.0, 4.0, 1.0, 1.0],
            }
        },
        "test_input": {
            "image": [
                [0, 1, 1, 0, 0, 0, 0, 0],
                [0, 1, 1, 0, 0, 1, 0, 0],
                [0, 0, 0, 0, 0, 1, 0, 0],
                [1, 1, 1, 1, 0, 1, 0, 0],
            ],
            "threshold": 0.45,
        },
    },
    "transcribe": {
        "hyperparams": {},
        "dataset": {
            "lexicon": {
                "hello": [0.38, 0.28, 0.52],
                "tblinc": [0.75, 0.95, 0.82],
                "start": [0.55, 0.55, 0.70],
                "stop": [0.22, 0.15, 0.30],
                "train": [0.65, 0.70, 0.85],
                "silence": [0.02, 0.05, 0.04],
            }
        },
        "test_input": {
            "frames": [
                [0.2, 0.5, 0.2, -0.4, -0.5, -0.2, 0.3, 0.5],
                [0.8, -0.8, 0.7, -0.7, 0.8, -0.8, 0.7, -0.7],
            ]
        },
    },
    "audio": {
        "hyperparams": {"lr": 0.2, "epochs": 140},
        "dataset": {},
        "test_input": {"freq_hz": 240, "sample_rate": 1000},
    },
    "multimodal": {
        "hyperparams": {"embed_dim": 16, "lr": 0.08, "epochs": 60},
        "dataset": {},
        "test_input": {
            "image": [
                [0, 0, 1, 0, 0],
                [0, 1, 1, 1, 0],
                [1, 1, 1, 1, 1],
                [0, 1, 1, 1, 0],
                [0, 0, 1, 0, 0],
            ],
            "question": "What shape is shown in this image?",
        },
    },
    "video": {
        "hyperparams": {"lr": 0.25, "epochs": 120},
        "dataset": {},
        "test_input": {
            "frames": [
                [[1, 0, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0]],
                [[0, 1, 0, 0], [0, 1, 0, 0], [0, 0, 0, 0]],
                [[0, 0, 1, 0], [0, 0, 1, 0], [0, 0, 0, 0]],
                [[0, 0, 0, 1], [0, 0, 0, 1], [0, 0, 0, 0]],
            ]
        },
    },
}


def get_training_presets() -> dict[str, dict[str, Any]]:
    """Build presets dictionary covering all 25 registered models."""
    presets: dict[str, dict[str, Any]] = {}
    for meta in list_models():
        key = meta["key"]
        if key in TRAINING_PRESETS:
            presets[key] = TRAINING_PRESETS[key]
        else:
            presets[key] = {
                "hyperparams": {},
                "dataset": {},
                "test_input": meta.get("input_example") or {},
            }
    return presets


def _filter_kwargs(fn: Any, raw: dict[str, Any]) -> dict[str, Any]:
    sig = inspect.signature(fn)
    valid = {}
    for k, v in raw.items():
        if k in sig.parameters:
            valid[k] = tuple(v) if k == "hidden_sizes" and isinstance(v, list) else v
    return valid


def train_and_persist_model(
    *,
    model_key: str,
    run_name: str = "",
    hyperparams: dict[str, Any] | None = None,
    dataset: dict[str, Any] | None = None,
    device_pref: str = "auto",
    artifacts_dir: str | Path = ".tblinc_artifacts",
) -> TrainingRun:
    """Train any registered AI model with optional custom hyperparams/dataset, save weights & log ORM run."""
    t0 = time.perf_counter()
    hp = dict(hyperparams or {})
    ds = dict(dataset or {})
    device = select_device(device_pref)

    cls = registry.get(model_key)
    init_kwargs = _filter_kwargs(cls.__init__, hp)
    model = create_model(model_key, **init_kwargs)

    # Dispatch training on custom dataset when supplied, or fall back to built-in model demo dataset
    if not ds:
        model.demo()
    elif "X" in ds and "y" in ds:
        model.fit(ds["X"], ds["y"])
    elif "X" in ds:
        model.fit(ds["X"])
    elif "texts" in ds and "labels" in ds:
        model.fit(ds["texts"], ds["labels"])
    elif "texts" in ds:
        model.fit(ds["texts"])
    elif "prototypes" in ds:
        model.fit(ds["prototypes"])
    elif "lexicon" in ds:
        model.fit(ds["lexicon"])
    elif "corpus" in ds:
        fit_kw = _filter_kwargs(model.fit, hp)
        model.fit(ds["corpus"], **fit_kw)
    elif "documents" in ds:
        model.fit(ds["documents"])
    elif "series" in ds:
        model.fit(ds["series"])
    elif "interactions" in ds:
        triples = [(str(r[0]), str(r[1]), float(r[2])) for r in ds["interactions"]]
        model.fit(triples)
    elif "images" in ds and "labels" in ds:
        model.fit(ds["images"], ds["labels"])
    elif "pairs" in ds:
        pairs = [(p[0], str(p[1])) for p in ds["pairs"]]
        model.fit(pairs)
    elif "samples" in ds:
        model.fit(ds["samples"])
    elif "signals" in ds and "labels" in ds:
        model.fit(ds["signals"], ds["labels"])
    elif "clips" in ds and "labels" in ds:
        model.fit(ds["clips"], ds["labels"])
    elif "voice_profiles" in ds:
        model.fit(ds["voice_profiles"])
    elif "custom_moods" in ds:
        model.fit(ds["custom_moods"])
    else:
        model.demo()

    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    run = TrainingRun(
        run_name=run_name.strip() or f"{model.metadata.name} Run",
        model_key=model_key,
        device=device,
        status="completed",
        hyperparams=hp,
        metrics=model.training_metrics,
        artifact_path="",
        duration_ms=elapsed_ms,
    )
    run.save()

    art_dir = Path(artifacts_dir)
    art_dir.mkdir(parents=True, exist_ok=True)
    art_file = art_dir / f"{model_key}_run_{run.pk}.json"
    model.save(art_file)
    run.artifact_path = str(art_file)
    run.save()
    return run


_LIVE_MODEL_CACHE: dict[str, tuple[str, Any]] = {}


def load_or_fit_live_model(model_key: str) -> tuple[Any, str]:
    """Load the latest trained checkpoint from TrainingRun (if available) or fit and cache the default model."""
    canonical = registry.resolve_key(model_key)
    cls = registry.get(canonical)
    try:
        latest = TrainingRun.objects.filter(model_key=canonical, status="completed").order_by("-id").first()
        if latest and latest.artifact_path:
            art_path = Path(latest.artifact_path)
            if art_path.is_file():
                cache_tag = f"run:{latest.pk}:{art_path.stat().st_mtime_ns}"
                cached = _LIVE_MODEL_CACHE.get(canonical)
                if cached and cached[0] == cache_tag:
                    return cached[1], f"checkpoint:{latest.run_name} (#{latest.pk})"
                loaded = cls.load(art_path)
                _LIVE_MODEL_CACHE[canonical] = (cache_tag, loaded)
                return loaded, f"checkpoint:{latest.run_name} (#{latest.pk})"
    except Exception:
        pass

    cached = _LIVE_MODEL_CACHE.get(canonical)
    if cached and cached[0] == "default":
        return cached[1], "builtin-trained"

    instance = cls()
    instance.demo()
    _LIVE_MODEL_CACHE[canonical] = ("default", instance)
    return instance, "builtin-trained"


def predict_from_training_run(run: TrainingRun, custom_input: Any = None) -> dict[str, Any]:
    """Load saved weights from a TrainingRun artifact and execute inference."""
    cls = registry.get(run.model_key)
    art = Path(run.artifact_path)
    if not art.is_file():
        raise FileNotFoundError(f"Saved weights not found at {art}")
    model = cls.load(art)
    inp = custom_input if custom_input is not None else model.metadata.input_example
    res = model.predict(inp)
    return {
        "run_id": run.pk,
        "run_name": run.run_name,
        "model_key": run.model_key,
        "artifact_path": run.artifact_path,
        "result": res.to_dict(),
    }
