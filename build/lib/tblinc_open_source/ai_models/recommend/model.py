"""14. MatrixFactorizationRecommender: SGD collaborative filtering recommender."""

from __future__ import annotations

import math
import random
import time
from typing import Any

from ..core import BaseAIModel, ModelMetadata, PredictionResult, register_model, timed_predict


@register_model
class MatrixFactorizationRecommender(BaseAIModel):
    """Latent-factor SGD Matrix Factorization with user/item biases and top-K ranking."""

    metadata = ModelMetadata(
        key="recommend",
        name="Smart Recommender",
        category="Recommendation Systems",
        task="Top-K Collaborative Filtering",
        description="Learns latent user and item embeddings via regularized SGD to recommend top items.",
        input_example={"user": "alice", "top_k": 3},
        tags=["recommender", "collaborative-filtering", "embeddings"],
    )

    def __init__(self, n_factors: int = 8, lr: float = 0.03, reg: float = 0.02, epochs: int = 120, seed: int = 42) -> None:
        super().__init__()
        self.n_factors = max(2, n_factors)
        self.lr = lr
        self.reg = reg
        self.epochs = epochs
        self.seed = seed
        self.global_mean: float = 0.0
        self.user_factors: dict[str, list[float]] = {}
        self.item_factors: dict[str, list[float]] = {}
        self.user_bias: dict[str, float] = {}
        self.item_bias: dict[str, float] = {}
        self.seen_by_user: dict[str, list[str]] = {}

    def _score_pair(self, user: str, item: str) -> float:
        u_vec = self.user_factors.get(user)
        i_vec = self.item_factors.get(item)
        dot = sum(a * b for a, b in zip(u_vec, i_vec)) if (u_vec and i_vec) else 0.0
        return self.global_mean + self.user_bias.get(user, 0.0) + self.item_bias.get(item, 0.0) + dot

    def fit(self, interactions: list[tuple[str, str, float]]) -> MatrixFactorizationRecommender:
        if not interactions:
            raise ValueError("interactions must be a non-empty list of (user, item, rating) tuples.")
        rng = random.Random(self.seed)
        users = sorted({str(u) for u, _, _ in interactions})
        items = sorted({str(i) for _, i, _ in interactions})
        self.global_mean = sum(float(r) for _, _, r in interactions) / len(interactions)

        scale = 0.2
        self.user_factors = {u: [rng.uniform(-scale, scale) for _ in range(self.n_factors)] for u in users}
        self.item_factors = {i: [rng.uniform(-scale, scale) for _ in range(self.n_factors)] for i in items}
        self.user_bias = {u: 0.0 for u in users}
        self.item_bias = {i: 0.0 for i in items}
        seen: dict[str, set[str]] = {u: set() for u in users}
        for u, i, _ in interactions:
            seen[str(u)].add(str(i))
        self.seen_by_user = {u: sorted(v) for u, v in seen.items()}

        triples = [(str(u), str(i), float(r)) for u, i, r in interactions]
        for _ in range(self.epochs):
            rng.shuffle(triples)
            for u, i, r in triples:
                pred = self._score_pair(u, i)
                err = r - pred
                self.user_bias[u] += self.lr * (err - self.reg * self.user_bias[u])
                self.item_bias[i] += self.lr * (err - self.reg * self.item_bias[i])
                uf = self.user_factors[u]
                itf = self.item_factors[i]
                for f in range(self.n_factors):
                    u_old, i_old = uf[f], itf[f]
                    uf[f] += self.lr * (err * i_old - self.reg * u_old)
                    itf[f] += self.lr * (err * u_old - self.reg * i_old)

        rmse = math.sqrt(sum((r - self._score_pair(u, i)) ** 2 for u, i, r in triples) / len(triples))
        self.is_fitted = True
        self.trained_at = time.time()
        self.training_metrics = {
            "users": len(users),
            "items": len(items),
            "interactions": len(triples),
            "train_rmse": round(rmse, 4),
        }
        return self

    @timed_predict
    def predict(self, data: str | dict[str, Any], top_k: int = 3) -> PredictionResult:
        if not self.is_fitted:
            raise RuntimeError("MatrixFactorizationRecommender must be fitted before predict().")
        if isinstance(data, dict):
            user = str(data.get("user", ""))
            top_k = int(data.get("top_k", top_k))
            exclude_seen = bool(data.get("exclude_seen", True))
        else:
            user = str(data)
            exclude_seen = True

        seen = set(self.seen_by_user.get(user, [])) if exclude_seen else set()
        candidates = [item for item in self.item_factors if item not in seen]
        if not candidates:
            candidates = list(self.item_factors.keys())
        ranked = sorted(
            ((item, round(self._score_pair(user, item), 4)) for item in candidates),
            key=lambda kv: kv[1],
            reverse=True,
        )[: max(1, top_k)]
        top_items = [{"item": item, "predicted_rating": score} for item, score in ranked]
        conf = min(1.0, max(0.0, ranked[0][1] / 5.0)) if ranked else 0.0
        return PredictionResult(
            model=self.metadata.key,
            prediction=[entry["item"] for entry in top_items],
            confidence=round(conf, 4),
            details={"user": user, "recommendations": top_items},
        )

    def get_state(self) -> dict[str, Any]:
        return {
            "n_factors": self.n_factors,
            "lr": self.lr,
            "reg": self.reg,
            "epochs": self.epochs,
            "seed": self.seed,
            "global_mean": self.global_mean,
            "user_factors": self.user_factors,
            "item_factors": self.item_factors,
            "user_bias": self.user_bias,
            "item_bias": self.item_bias,
            "seen_by_user": self.seen_by_user,
        }

    def set_state(self, state: dict[str, Any]) -> None:
        self.n_factors = int(state["n_factors"])
        self.lr = float(state["lr"])
        self.reg = float(state["reg"])
        self.epochs = int(state["epochs"])
        self.seed = int(state["seed"])
        self.global_mean = float(state["global_mean"])
        self.user_factors = state["user_factors"]
        self.item_factors = state["item_factors"]
        self.user_bias = state["user_bias"]
        self.item_bias = state["item_bias"]
        self.seen_by_user = state["seen_by_user"]

    def _run_demo(self, custom_input: Any = None) -> dict[str, Any]:
        interactions = [
            ("alice", "llm_kit", 5.0), ("alice", "rag_studio", 4.8), ("alice", "vision_pro", 2.0),
            ("bob", "llm_kit", 4.9), ("bob", "rag_studio", 4.6), ("bob", "agent_sdk", 5.0),
            ("carol", "vision_pro", 5.0), ("carol", "audio_asr", 4.7), ("carol", "video_gen", 4.9),
            ("dave", "vision_pro", 4.8), ("dave", "video_gen", 4.5), ("dave", "llm_kit", 2.5),
            ("eve", "rag_studio", 4.7), ("eve", "agent_sdk", 4.9), ("eve", "tabular_ml", 4.4),
        ]
        self.fit(interactions)
        res = self.predict(custom_input or self.metadata.input_example)
        return {"training": self.training_metrics, "result": res.to_dict()}
