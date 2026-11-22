"""5. VisionConvNet: 2D convolutional filter bank + max pooling + softmax image classifier."""

from __future__ import annotations

import math
import time
from typing import Any

from ..core import BaseAIModel, ModelMetadata, PredictionResult, register_model, timed_predict

# Built-in 3x3 convolutional kernels: horizontal edge, vertical edge, Laplacian, sharpening
_KERNELS: dict[str, list[list[float]]] = {
    "sobel_x": [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]],
    "sobel_y": [[-1, -2, -1], [0, 0, 0], [1, 2, 1]],
    "laplacian": [[0, -1, 0], [-1, 4, -1], [0, -1, 0]],
    "diag_pos": [[0, 1, 2], [-1, 0, 1], [-2, -1, 0]],
    "diag_neg": [[2, 1, 0], [1, 0, -1], [0, -1, -2]],
}


def _conv2d_relu(grid: list[list[float]], kernel: list[list[float]]) -> list[list[float]]:
    h, w = len(grid), len(grid[0])
    out: list[list[float]] = []
    for r in range(max(1, h - 2)):
        row: list[float] = []
        for c in range(max(1, w - 2)):
            acc = 0.0
            for kr in range(3):
                for kc in range(3):
                    rr = min(r + kr, h - 1)
                    cc = min(c + kc, w - 1)
                    acc += grid[rr][cc] * kernel[kr][kc]
            row.append(max(0.0, acc))
        out.append(row)
    return out


def _global_pool(fmap: list[list[float]]) -> tuple[float, float]:
    vals = [v for row in fmap for v in row]
    if not vals:
        return 0.0, 0.0
    return max(vals), sum(vals) / len(vals)


@register_model
class VisionConvNet(BaseAIModel):
    """2D Convolutional feature extractor (Sobel/Laplacian/Diagonal + ReLU + Pooling) & Softmax head."""

    metadata = ModelMetadata(
        key="vision",
        name="Image Recognition AI",
        category="Computer Vision",
        task="2D Image Pattern & Shape Classification",
        description="Applies 2D convolutional filter banks, ReLU, pooling, and a trained softmax head on 2D grids.",
        input_example={
            "image": [
                [0, 0, 1, 0, 0],
                [0, 0, 1, 0, 0],
                [1, 1, 1, 1, 1],
                [0, 0, 1, 0, 0],
                [0, 0, 1, 0, 0],
            ]
        },
        tags=["vision", "cnn", "conv2d", "image"],
    )

    def __init__(self, lr: float = 0.15, epochs: int = 120) -> None:
        super().__init__()
        self.lr = lr
        self.epochs = epochs
        self.classes: list[str] = []
        self.weights: list[list[float]] = []
        self.biases: list[float] = []

    def extract_features(self, image: list[list[float]]) -> list[float]:
        grid = [[float(px) for px in row] for row in image]
        h, w = len(grid), len(grid[0])
        flat = [px for row in grid for px in row]
        mean_val = sum(flat) / max(1, len(flat))
        var_val = sum((px - mean_val) ** 2 for px in flat) / max(1, len(flat))
        center_r, center_c = h // 2, w // 2
        row_energy = sum(grid[center_r]) / max(1, w)
        col_energy = sum(grid[r][center_c] for r in range(h)) / max(1, h)
        diag_energy = sum(grid[i][i] for i in range(min(h, w))) / max(1, min(h, w))

        feats = [mean_val, math.sqrt(var_val), row_energy, col_energy, diag_energy]
        for kernel in _KERNELS.values():
            fmap = _conv2d_relu(grid, kernel)
            mx, avg = _global_pool(fmap)
            feats.extend([mx / 4.0, avg / 4.0])
        return feats

    def _softmax(self, logits: list[float]) -> list[float]:
        m = max(logits)
        exps = [math.exp(v - m) for v in logits]
        s = sum(exps) or 1.0
        return [e / s for e in exps]

    def fit(self, images: list[list[list[float]]], labels: list[str]) -> VisionConvNet:
        if not images or len(images) != len(labels):
            raise ValueError("images and labels must be non-empty and match in length.")
        X = [self.extract_features(img) for img in images]
        dim = len(X[0])
        self.classes = sorted(set(labels))
        c2i = {c: i for i, c in enumerate(self.classes)}
        n_cls = len(self.classes)
        self.weights = [[0.0] * dim for _ in range(n_cls)]
        self.biases = [0.0] * n_cls

        n = len(X)
        for _ in range(self.epochs):
            gw = [[0.0] * dim for _ in range(n_cls)]
            gb = [0.0] * n_cls
            for xi, yi in zip(X, labels):
                logits = [
                    sum(w * v for w, v in zip(self.weights[c], xi)) + self.biases[c]
                    for c in range(n_cls)
                ]
                probs = self._softmax(logits)
                t = c2i[yi]
                for c in range(n_cls):
                    err = probs[c] - (1.0 if c == t else 0.0)
                    gb[c] += err
                    for d in range(dim):
                        gw[c][d] += err * xi[d]
            for c in range(n_cls):
                self.biases[c] -= self.lr * (gb[c] / n)
                for d in range(dim):
                    self.weights[c][d] -= self.lr * ((gw[c][d] / n) + 0.005 * self.weights[c][d])

        self.is_fitted = True
        self.trained_at = time.time()
        acc = self.evaluate(images, labels)["accuracy"]
        self.training_metrics = {"classes": self.classes, "feature_dim": dim, "train_accuracy": acc}
        return self

    @timed_predict
    def predict(self, data: list[list[float]] | dict[str, Any]) -> PredictionResult:
        if not self.is_fitted:
            raise RuntimeError("VisionConvNet must be fitted before predict().")
        image = data["image"] if isinstance(data, dict) else data
        feats = self.extract_features(image)
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
            details={"probabilities": {c: round(p, 4) for c, p in zip(self.classes, probs)}},
        )

    def evaluate(self, images: list[list[list[float]]], labels: list[str]) -> dict[str, Any]:
        correct = sum(1 for img, y in zip(images, labels) if self.predict(img).prediction == y)
        return {"accuracy": round(correct / max(1, len(labels)), 4), "samples": len(labels)}

    def get_state(self) -> dict[str, Any]:
        return {
            "lr": self.lr,
            "epochs": self.epochs,
            "classes": self.classes,
            "weights": self.weights,
            "biases": self.biases,
        }

    def set_state(self, state: dict[str, Any]) -> None:
        self.lr = float(state["lr"])
        self.epochs = int(state["epochs"])
        self.classes = list(state["classes"])
        self.weights = state["weights"]
        self.biases = list(state["biases"])

    def _run_demo(self, custom_input: Any = None) -> dict[str, Any]:
        plus = [
            [0, 0, 1, 0, 0],
            [0, 0, 1, 0, 0],
            [1, 1, 1, 1, 1],
            [0, 0, 1, 0, 0],
            [0, 0, 1, 0, 0],
        ]
        horiz = [
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [1, 1, 1, 1, 1],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ]
        diag = [
            [1, 0, 0, 0, 0],
            [0, 1, 0, 0, 0],
            [0, 0, 1, 0, 0],
            [0, 0, 0, 1, 0],
            [0, 0, 0, 0, 1],
        ]
        box = [
            [1, 1, 1, 1, 1],
            [1, 0, 0, 0, 1],
            [1, 0, 0, 0, 1],
            [1, 0, 0, 0, 1],
            [1, 1, 1, 1, 1],
        ]
        self.fit([plus, horiz, diag, box], ["plus", "horizontal_bar", "diagonal", "square"])
        res = self.predict(custom_input or self.metadata.input_example)
        return {"training": self.training_metrics, "result": res.to_dict()}
