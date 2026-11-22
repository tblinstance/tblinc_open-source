"""19. VideoMotionModel: Temporal 3D frame-sequence optical-flow & action classifier."""

from __future__ import annotations

import math
import time
from typing import Any

from ..core import BaseAIModel, ModelMetadata, PredictionResult, register_model, timed_predict


def _centroid(frame: list[list[float]]) -> tuple[float, float, float]:
    h, w = len(frame), len(frame[0])
    mass = 0.0
    rx = 0.0
    ry = 0.0
    for r in range(h):
        for c in range(w):
            val = float(frame[r][c])
            mass += val
            ry += r * val
            rx += c * val
    if mass <= 1e-9:
        return (w - 1) / 2.0, (h - 1) / 2.0, 0.0
    return rx / mass, ry / mass, mass / (h * w)


@register_model
class VideoMotionModel(BaseAIModel):
    """Analyzes 3D video clips [T][H][W] via temporal frame diffs and centroid optical-flow velocity."""

    metadata = ModelMetadata(
        key="video",
        name="AI Video Generator",
        category="Video AI",
        task="Temporal Motion & Action Classification",
        description="Extracts temporal frame differences, centroid velocity trajectories, and classifies video actions.",
        input_example={
            "frames": [
                [[1, 0, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0]],
                [[0, 1, 0, 0], [0, 1, 0, 0], [0, 0, 0, 0]],
                [[0, 0, 1, 0], [0, 0, 1, 0], [0, 0, 0, 0]],
                [[0, 0, 0, 1], [0, 0, 0, 1], [0, 0, 0, 0]],
            ]
        },
        tags=["video", "motion", "temporal", "action-recognition"],
    )

    def __init__(self, lr: float = 0.25, epochs: int = 120) -> None:
        super().__init__()
        self.lr = lr
        self.epochs = epochs
        self.classes: list[str] = []
        self.weights: list[list[float]] = []
        self.biases: list[float] = []

    def extract_motion_features(self, frames: list[list[list[float]]]) -> tuple[list[float], dict[str, float]]:
        if len(frames) < 2:
            raise ValueError("Video clip must contain at least 2 frames.")
        centroids = [_centroid(f) for f in frames]
        dxs = [centroids[i + 1][0] - centroids[i][0] for i in range(len(centroids) - 1)]
        dys = [centroids[i + 1][1] - centroids[i][1] for i in range(len(centroids) - 1)]
        dmass = [centroids[i + 1][2] - centroids[i][2] for i in range(len(centroids) - 1)]

        diffs: list[float] = []
        for i in range(len(frames) - 1):
            f1, f2 = frames[i], frames[i + 1]
            h, w = len(f1), len(f1[0])
            dval = sum(abs(float(f2[r][c]) - float(f1[r][c])) for r in range(h) for c in range(w)) / max(1, h * w)
            diffs.append(dval)

        mean_dx = sum(dxs) / len(dxs)
        mean_dy = sum(dys) / len(dys)
        mean_diff = sum(diffs) / len(diffs)
        mean_dmass = sum(dmass) / len(dmass)
        speed = math.sqrt(mean_dx * mean_dx + mean_dy * mean_dy)
        feats = [mean_dx, mean_dy, mean_diff, mean_dmass, speed]
        summary = {
            "frames": len(frames),
            "avg_dx": round(mean_dx, 4),
            "avg_dy": round(mean_dy, 4),
            "motion_energy": round(mean_diff, 4),
        }
        return feats, summary

    def _softmax(self, logits: list[float]) -> list[float]:
        mx = max(logits)
        exps = [math.exp(v - mx) for v in logits]
        s = sum(exps) or 1.0
        return [e / s for e in exps]

    def fit(self, clips: list[list[list[list[float]]]], labels: list[str]) -> VideoMotionModel:
        if not clips or len(clips) != len(labels):
            raise ValueError("clips and labels must be non-empty and match in length.")
        X = [self.extract_motion_features(c)[0] for c in clips]
        d = len(X[0])
        self.classes = sorted(set(labels))
        c2i = {c: i for i, c in enumerate(self.classes)}
        k = len(self.classes)
        self.weights = [[0.0] * d for _ in range(k)]
        self.biases = [0.0] * k

        n = len(X)
        for _ in range(self.epochs):
            gw = [[0.0] * d for _ in range(k)]
            gb = [0.0] * k
            for xi, yi in zip(X, labels):
                logits = [sum(w * v for w, v in zip(self.weights[c], xi)) + self.biases[c] for c in range(k)]
                probs = self._softmax(logits)
                t = c2i[yi]
                for c in range(k):
                    err = probs[c] - (1.0 if c == t else 0.0)
                    gb[c] += err
                    for j in range(d):
                        gw[c][j] += err * xi[j]
            for c in range(k):
                self.biases[c] -= self.lr * (gb[c] / n)
                for j in range(d):
                    self.weights[c][j] -= self.lr * ((gw[c][j] / n) + 0.005 * self.weights[c][j])

        self.is_fitted = True
        self.trained_at = time.time()
        acc = self.evaluate(clips, labels)["accuracy"]
        self.training_metrics = {"classes": self.classes, "train_accuracy": acc, "clips": n}
        return self

    @timed_predict
    def predict(self, data: list[list[list[float]]] | dict[str, Any]) -> PredictionResult:
        if not self.is_fitted:
            raise RuntimeError("VideoMotionModel must be fitted before predict().")
        frames = data["frames"] if isinstance(data, dict) else data
        feats, summary = self.extract_motion_features(frames)
        logits = [
            sum(w * v for w, v in zip(self.weights[c], feats)) + self.biases[c]
            for c in range(len(self.classes))
        ]
        probs = self._softmax(logits)
        best = max(range(len(probs)), key=lambda i: probs[i])
        return PredictionResult(
            model=self.metadata.key,
            prediction=self.classes[best],
            confidence=round(probs[best], 4),
            details={"probabilities": {c: round(p, 4) for c, p in zip(self.classes, probs)}, "motion": summary},
        )

    def evaluate(self, clips: list[list[list[list[float]]]], labels: list[str]) -> dict[str, Any]:
        correct = sum(1 for clip, y in zip(clips, labels) if self.predict(clip).prediction == y)
        return {"accuracy": round(correct / max(1, len(labels)), 4), "samples": len(labels)}

    def synthesize_sequence(
        self,
        prompt: str = "neon wave",
        motion: str = "pan_right",
        num_frames: int = 24,
        fps: int = 12,
    ) -> dict[str, Any]:
        """Generate a multi-frame procedural AI video clip specification + motion grid for canvas playback."""
        n = max(6, min(60, int(num_frames)))
        fps = max(4, min(30, int(fps)))
        motion_frames: list[list[list[float]]] = []
        keyframes: list[dict[str, Any]] = []

        for i in range(n):
            t = i / max(1, n - 1)
            if motion == "pan_left":
                cx, cy, radius = 0.85 - 0.70 * t, 0.5 + 0.12 * math.sin(t * math.pi * 2), 0.18
            elif motion == "zoom_in":
                cx, cy, radius = 0.5, 0.5, 0.10 + 0.28 * t
            elif motion == "orbit":
                cx = 0.5 + 0.26 * math.cos(t * math.pi * 2)
                cy = 0.5 + 0.22 * math.sin(t * math.pi * 2)
                radius = 0.16 + 0.04 * math.sin(t * math.pi * 4)
            elif motion == "static":
                cx, cy, radius = 0.5, 0.5, 0.18
            else:
                cx, cy, radius = 0.15 + 0.70 * t, 0.5 + 0.12 * math.sin(t * math.pi * 2), 0.18

            grid: list[list[float]] = []
            for r in range(3):
                row: list[float] = []
                for c in range(4):
                    dist = math.sqrt(((c + 0.5) / 4.0 - cx) ** 2 + ((r + 0.5) / 3.0 - cy) ** 2)
                    row.append(1.0 if dist <= radius * 1.45 else 0.0)
                grid.append(row)
            motion_frames.append(grid)
            keyframes.append(
                {
                    "frame": i,
                    "cx": round(cx, 4),
                    "cy": round(cy, 4),
                    "radius": round(radius, 4),
                    "hue": int((210 + 130 * t) % 360),
                }
            )

        analysis = self.predict({"frames": motion_frames[:8]}) if self.is_fitted else None
        return {
            "prompt": prompt,
            "motion": motion,
            "fps": fps,
            "num_frames": n,
            "duration_sec": round(n / fps, 2),
            "keyframes": keyframes,
            "analysis": analysis.to_dict() if analysis else None,
        }

    def get_state(self) -> dict[str, Any]:
        return {"lr": self.lr, "epochs": self.epochs, "classes": self.classes, "weights": self.weights, "biases": self.biases}

    def set_state(self, state: dict[str, Any]) -> None:
        self.lr = float(state["lr"])
        self.epochs = int(state["epochs"])
        self.classes = list(state["classes"])
        self.weights = state["weights"]
        self.biases = list(state["biases"])

    def _run_demo(self, custom_input: Any = None) -> dict[str, Any]:
        pan_right = [
            [[1, 0, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0]],
            [[0, 1, 0, 0], [0, 1, 0, 0], [0, 0, 0, 0]],
            [[0, 0, 1, 0], [0, 0, 1, 0], [0, 0, 0, 0]],
            [[0, 0, 0, 1], [0, 0, 0, 1], [0, 0, 0, 0]],
        ]
        pan_left = list(reversed(pan_right))
        static_clip = [
            [[0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]]
            for _ in range(4)
        ]
        zoom_in = [
            [[0, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 0]],
            [[0, 1, 0, 0], [1, 1, 1, 0], [0, 1, 0, 0]],
            [[1, 1, 1, 0], [1, 1, 1, 1], [1, 1, 1, 0]],
            [[1, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1]],
        ]
        self.fit([pan_right, pan_left, static_clip, zoom_in], ["pan_right", "pan_left", "static", "zoom_in"])
        res = self.predict(custom_input or self.metadata.input_example)
        return {"training": self.training_metrics, "result": res.to_dict()}
