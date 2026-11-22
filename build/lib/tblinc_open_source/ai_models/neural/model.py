"""2. MLPNeuralNet: Multi-Layer Perceptron deep neural network with backpropagation & Adam."""

from __future__ import annotations

import math
import random
import time
from typing import Any

from ..core import BaseAIModel, ModelMetadata, PredictionResult, register_model, timed_predict


def _relu(x: float) -> float:
    return x if x > 0.0 else 0.0


def _relu_deriv(x: float) -> float:
    return 1.0 if x > 0.0 else 0.0


def _softmax(logits: list[float]) -> list[float]:
    m = max(logits)
    exps = [math.exp(v - m) for v in logits]
    s = sum(exps) or 1.0
    return [e / s for e in exps]


@register_model
class MLPNeuralNet(BaseAIModel):
    """Feed-forward Multi-Layer Perceptron classifier built from scratch with Adam & ReLU."""

    metadata = ModelMetadata(
        key="neural",
        name="Deep Neural Network",
        category="Deep Learning",
        task="Multi-class Classification",
        description="Multi-layer perceptron with He init, ReLU hidden layers, softmax output, and Adam backprop.",
        input_example={"features": [0.9, 0.85, 0.1, 0.2]},
        tags=["deep-learning", "mlp", "neural-network", "backprop"],
    )

    def __init__(
        self,
        hidden_sizes: tuple[int, ...] = (12, 8),
        lr: float = 0.02,
        epochs: int = 80,
        seed: int = 42,
    ) -> None:
        super().__init__()
        self.hidden_sizes = list(hidden_sizes)
        self.lr = lr
        self.epochs = epochs
        self.seed = seed
        self.classes: list[Any] = []
        self.weights: list[list[list[float]]] = []  # [layer][out][in]
        self.biases: list[list[float]] = []

    def _init_layers(self, in_dim: int, out_dim: int) -> None:
        rng = random.Random(self.seed)
        dims = [in_dim, *self.hidden_sizes, out_dim]
        self.weights = []
        self.biases = []
        for fan_in, fan_out in zip(dims[:-1], dims[1:]):
            std = math.sqrt(2.0 / max(1, fan_in))
            w = [[rng.gauss(0.0, std) for _ in range(fan_in)] for _ in range(fan_out)]
            b = [0.0 for _ in range(fan_out)]
            self.weights.append(w)
            self.biases.append(b)

    def _forward(self, x: list[float]) -> tuple[list[list[float]], list[list[float]]]:
        activations = [list(x)]
        pre_acts: list[list[float]] = []
        cur = list(x)
        for li, (w, b) in enumerate(zip(self.weights, self.biases)):
            z = [sum(wij * cj for wij, cj in zip(row, cur)) + bi for row, bi in zip(w, b)]
            pre_acts.append(z)
            if li < len(self.weights) - 1:
                cur = [_relu(v) for v in z]
            else:
                cur = _softmax(z)
            activations.append(cur)
        return pre_acts, activations

    def fit(self, X: list[list[float]], y: list[Any]) -> MLPNeuralNet:
        if not X or len(X) != len(y):
            raise ValueError("X and y must be non-empty and have matching lengths.")
        in_dim = len(X[0])
        self.classes = sorted(set(y), key=lambda v: str(v))
        class_to_idx = {c: i for i, c in enumerate(self.classes)}
        out_dim = len(self.classes)
        self._init_layers(in_dim, out_dim)

        # Adam moment buffers
        m_w = [[[0.0] * len(row) for row in layer] for layer in self.weights]
        v_w = [[[0.0] * len(row) for row in layer] for layer in self.weights]
        m_b = [[0.0] * len(layer) for layer in self.biases]
        v_b = [[0.0] * len(layer) for layer in self.biases]
        beta1, beta2, eps = 0.9, 0.999, 1e-8

        n = len(X)
        final_loss = 0.0
        for epoch in range(1, self.epochs + 1):
            grad_w = [[[0.0] * len(row) for row in layer] for layer in self.weights]
            grad_b = [[0.0] * len(layer) for layer in self.biases]
            epoch_loss = 0.0

            for xi, yi in zip(X, y):
                target = class_to_idx[yi]
                pre_acts, acts = self._forward(xi)
                probs = acts[-1]
                epoch_loss += -math.log(max(probs[target], 1e-12))

                # Output layer gradient: softmax + cross-entropy
                delta = [p - (1.0 if j == target else 0.0) for j, p in enumerate(probs)]
                for li in range(len(self.weights) - 1, -1, -1):
                    prev_act = acts[li]
                    for j in range(len(delta)):
                        grad_b[li][j] += delta[j]
                        for k in range(len(prev_act)):
                            grad_w[li][j][k] += delta[j] * prev_act[k]
                    if li > 0:
                        w_cur = self.weights[li]
                        z_prev = pre_acts[li - 1]
                        next_delta = []
                        for k in range(len(z_prev)):
                            s = sum(w_cur[j][k] * delta[j] for j in range(len(delta)))
                            next_delta.append(s * _relu_deriv(z_prev[k]))
                        delta = next_delta

            # Adam parameter update
            bc1 = 1.0 - beta1**epoch
            bc2 = 1.0 - beta2**epoch
            for li in range(len(self.weights)):
                for j in range(len(self.weights[li])):
                    gb = grad_b[li][j] / n
                    m_b[li][j] = beta1 * m_b[li][j] + (1.0 - beta1) * gb
                    v_b[li][j] = beta2 * v_b[li][j] + (1.0 - beta2) * (gb * gb)
                    self.biases[li][j] -= self.lr * (m_b[li][j] / bc1) / (math.sqrt(v_b[li][j] / bc2) + eps)
                    for k in range(len(self.weights[li][j])):
                        gw = grad_w[li][j][k] / n
                        m_w[li][j][k] = beta1 * m_w[li][j][k] + (1.0 - beta1) * gw
                        v_w[li][j][k] = beta2 * v_w[li][j][k] + (1.0 - beta2) * (gw * gw)
                        self.weights[li][j][k] -= (
                            self.lr * (m_w[li][j][k] / bc1) / (math.sqrt(v_w[li][j][k] / bc2) + eps)
                        )
            final_loss = epoch_loss / n

        self.is_fitted = True
        self.trained_at = time.time()
        acc = self.evaluate(X, y)["accuracy"]
        self.training_metrics = {
            "final_loss": round(final_loss, 4),
            "train_accuracy": acc,
            "layers": [in_dim, *self.hidden_sizes, out_dim],
        }
        return self

    @timed_predict
    def predict(self, data: list[float] | dict[str, Any]) -> PredictionResult:
        if not self.is_fitted:
            raise RuntimeError("MLPNeuralNet must be fitted before predict().")
        features = data["features"] if isinstance(data, dict) else data
        vec = [float(v) for v in features]
        _, acts = self._forward(vec)
        probs = acts[-1]
        best_idx = max(range(len(probs)), key=lambda i: probs[i])
        return PredictionResult(
            model=self.metadata.key,
            prediction=self.classes[best_idx],
            confidence=round(probs[best_idx], 4),
            details={"probabilities": {str(c): round(p, 4) for c, p in zip(self.classes, probs)}},
        )

    def evaluate(self, X: list[list[float]], y: list[Any]) -> dict[str, Any]:
        correct = 0
        for xi, yi in zip(X, y):
            if self.predict(xi).prediction == yi:
                correct += 1
        return {"accuracy": round(correct / max(1, len(y)), 4), "samples": len(y)}

    def get_state(self) -> dict[str, Any]:
        return {
            "hidden_sizes": self.hidden_sizes,
            "lr": self.lr,
            "epochs": self.epochs,
            "seed": self.seed,
            "classes": self.classes,
            "weights": self.weights,
            "biases": self.biases,
        }

    def set_state(self, state: dict[str, Any]) -> None:
        self.hidden_sizes = list(state["hidden_sizes"])
        self.lr = float(state["lr"])
        self.epochs = int(state["epochs"])
        self.seed = int(state["seed"])
        self.classes = list(state["classes"])
        self.weights = state["weights"]
        self.biases = state["biases"]

    def _run_demo(self, custom_input: Any = None) -> dict[str, Any]:
        X = [
            [0.95, 0.90, 0.10, 0.05],
            [0.85, 0.80, 0.15, 0.10],
            [0.10, 0.15, 0.90, 0.85],
            [0.05, 0.20, 0.85, 0.95],
            [0.50, 0.55, 0.50, 0.45],
            [0.45, 0.50, 0.55, 0.50],
        ]
        y = ["high_compute", "high_compute", "edge_light", "edge_light", "balanced", "balanced"]
        self.fit(X, y)
        res = self.predict(custom_input or self.metadata.input_example)
        return {"training": self.training_metrics, "result": res.to_dict()}
