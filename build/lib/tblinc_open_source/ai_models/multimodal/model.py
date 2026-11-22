"""15. MultimodalVLM: Contrastive Vision-Language Model (CLIP-style image-text alignment & VQA)."""

from __future__ import annotations

import math
import random
import re
import time
from typing import Any

from ..core import BaseAIModel, ModelMetadata, PredictionResult, register_model, timed_predict


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+", text.lower())


def _l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


@register_model
class MultimodalVLM(BaseAIModel):
    """Joint Vision-Language Model learning aligned visual and textual embeddings for VQA & matching."""

    metadata = ModelMetadata(
        key="multimodal",
        name="Vision-Language AI",
        category="VLM / Multimodal",
        task="Image-Text Matching & Visual QA",
        description="Projects 2D visual descriptors and text prompts into a shared contrastive embedding space.",
        input_example={
            "image": [
                [0, 0, 1, 0, 0],
                [0, 1, 1, 1, 0],
                [1, 1, 1, 1, 1],
                [0, 1, 1, 1, 0],
                [0, 0, 1, 0, 0],
            ],
            "question": "What shape is shown in this image?",
        },
        tags=["vlm", "multimodal", "vision", "clip", "vqa"],
    )

    def __init__(self, embed_dim: int = 16, lr: float = 0.08, epochs: int = 60, seed: int = 42) -> None:
        super().__init__()
        self.embed_dim = max(4, embed_dim)
        self.lr = lr
        self.epochs = epochs
        self.seed = seed
        self.vocab: list[str] = []
        self.vis_proj: list[list[float]] = []  # [embed_dim][vis_dim]
        self.txt_proj: list[list[float]] = []  # [embed_dim][vocab_size]
        self.captions: list[str] = []
        self.caption_embeds: list[list[float]] = []

    def _encode_visual_raw(self, image: list[list[float]]) -> list[float]:
        grid = [[float(v) for v in row] for row in image]
        h, w = len(grid), len(grid[0])
        flat = [v for row in grid for v in row]
        mean = sum(flat) / max(1, len(flat))
        border = (
            sum(grid[0])
            + sum(grid[-1])
            + sum(grid[r][0] + grid[r][-1] for r in range(1, max(1, h - 1)))
        ) / max(1, 2 * w + 2 * max(0, h - 2))
        center = grid[h // 2][w // 2]
        top_half = sum(v for row in grid[: max(1, h // 2)] for v in row) / max(1, (h // 2) * w)
        bot_half = sum(v for row in grid[h // 2 :] for v in row) / max(1, (h - h // 2) * w)
        left_half = sum(row[c] for row in grid for c in range(max(1, w // 2))) / max(1, h * (w // 2))
        right_half = sum(row[c] for row in grid for c in range(w // 2, w)) / max(1, h * (w - w // 2))
        diag = sum(grid[i][i] for i in range(min(h, w))) / max(1, min(h, w))
        anti_diag = sum(grid[i][w - 1 - i] for i in range(min(h, w))) / max(1, min(h, w))
        center_row = sum(grid[h // 2]) / max(1, w)
        center_col = sum(grid[r][w // 2] for r in range(h)) / max(1, h)
        return [mean, border, center, top_half, bot_half, left_half, right_half, diag, anti_diag, center_row, center_col]

    def _encode_text_bow(self, text: str) -> list[float]:
        toks = _words(text)
        vmap = {t: i for i, t in enumerate(self.vocab)}
        vec = [0.0] * len(self.vocab)
        for tok in toks:
            idx = vmap.get(tok)
            if idx is not None:
                vec[idx] += 1.0
        return _l2_normalize(vec)

    def _project(self, mat: list[list[float]], vec: list[float]) -> list[float]:
        raw = [sum(w * x for w, x in zip(row, vec)) for row in mat]
        return _l2_normalize(raw)

    def fit(self, pairs: list[tuple[list[list[float]], str]]) -> MultimodalVLM:
        if len(pairs) < 2:
            raise ValueError("MultimodalVLM requires at least 2 (image, caption) pairs.")

        rng = random.Random(self.seed)
        self.captions = [cap for _, cap in pairs]
        vocab_set = {tok for cap in self.captions for tok in _words(cap)}
        self.vocab = sorted(vocab_set)

        vis_raw = [self._encode_visual_raw(img) for img, _ in pairs]
        txt_raw = [self._encode_text_bow(cap) for cap in self.captions]
        vdim = len(vis_raw[0])
        tdim = max(1, len(self.vocab))

        scale_v = 1.0 / math.sqrt(vdim)
        scale_t = 1.0 / math.sqrt(tdim)
        self.vis_proj = [[rng.uniform(-scale_v, scale_v) for _ in range(vdim)] for _ in range(self.embed_dim)]
        self.txt_proj = [[rng.uniform(-scale_t, scale_t) for _ in range(tdim)] for _ in range(self.embed_dim)]

        # Contrastive alignment: pull paired (v_i, t_i) together, push mismatched pairs apart
        n = len(pairs)
        for _ in range(self.epochs):
            v_embs = [self._project(self.vis_proj, vr) for vr in vis_raw]
            t_embs = [self._project(self.txt_proj, tr) for tr in txt_raw]
            for i in range(n):
                for j in range(n):
                    sim = _dot(v_embs[i], t_embs[j])
                    target = 1.0 if i == j else -0.4
                    err = (target - sim) / n
                    for d in range(self.embed_dim):
                        tv = t_embs[j][d]
                        vv = v_embs[i][d]
                        for k in range(vdim):
                            self.vis_proj[d][k] += self.lr * err * tv * vis_raw[i][k]
                        for k in range(tdim):
                            self.txt_proj[d][k] += self.lr * err * vv * txt_raw[j][k]

        self.caption_embeds = [self._project(self.txt_proj, tr) for tr in txt_raw]
        self.is_fitted = True
        self.trained_at = time.time()
        acc = self.evaluate(pairs)["top1_retrieval_accuracy"]
        self.training_metrics = {
            "pairs_trained": n,
            "vocab_size": len(self.vocab),
            "embed_dim": self.embed_dim,
            "top1_retrieval_accuracy": acc,
        }
        return self

    @timed_predict
    def predict(self, data: dict[str, Any]) -> PredictionResult:
        if not self.is_fitted:
            raise RuntimeError("MultimodalVLM must be fitted before predict().")
        image = data.get("image")
        question = str(data.get("question", ""))
        candidate_labels = data.get("candidates")

        if image is None:
            raise ValueError("MultimodalVLM requires an 'image' 2D grid in input.")
        v_emb = self._project(self.vis_proj, self._encode_visual_raw(image))

        if candidate_labels:
            targets = list(candidate_labels)
            t_embs = [self._project(self.txt_proj, self._encode_text_bow(lbl)) for lbl in targets]
        else:
            targets = self.captions
            t_embs = self.caption_embeds

        sims = [_dot(v_emb, te) for te in t_embs]
        mx = max(sims)
        exps = [math.exp((s - mx) * 4.0) for s in sims]
        norm = sum(exps) or 1.0
        probs = [e / norm for e in exps]
        best_idx = max(range(len(sims)), key=lambda i: sims[i])
        best_caption = targets[best_idx]

        answer = f"{best_caption}" if not question else f"{best_caption} (Q: {question})"
        return PredictionResult(
            model=self.metadata.key,
            prediction=answer,
            confidence=round(probs[best_idx], 4),
            details={
                "matched_caption": best_caption,
                "similarities": {cap: round(s, 4) for cap, s in zip(targets, sims)},
            },
        )

    def evaluate(self, pairs: list[tuple[list[list[float]], str]]) -> dict[str, Any]:
        correct = 0
        for img, cap in pairs:
            res = self.predict({"image": img})
            if res.details.get("matched_caption") == cap:
                correct += 1
        return {"top1_retrieval_accuracy": round(correct / max(1, len(pairs)), 4), "samples": len(pairs)}

    def get_state(self) -> dict[str, Any]:
        return {
            "embed_dim": self.embed_dim,
            "lr": self.lr,
            "epochs": self.epochs,
            "seed": self.seed,
            "vocab": self.vocab,
            "vis_proj": self.vis_proj,
            "txt_proj": self.txt_proj,
            "captions": self.captions,
            "caption_embeds": self.caption_embeds,
        }

    def set_state(self, state: dict[str, Any]) -> None:
        self.embed_dim = int(state["embed_dim"])
        self.lr = float(state["lr"])
        self.epochs = int(state["epochs"])
        self.seed = int(state["seed"])
        self.vocab = list(state["vocab"])
        self.vis_proj = state["vis_proj"]
        self.txt_proj = state["txt_proj"]
        self.captions = list(state["captions"])
        self.caption_embeds = state["caption_embeds"]

    def _run_demo(self, custom_input: Any = None) -> dict[str, Any]:
        diamond = [
            [0, 0, 1, 0, 0],
            [0, 1, 1, 1, 0],
            [1, 1, 1, 1, 1],
            [0, 1, 1, 1, 0],
            [0, 0, 1, 0, 0],
        ]
        border_box = [
            [1, 1, 1, 1, 1],
            [1, 0, 0, 0, 1],
            [1, 0, 0, 0, 1],
            [1, 0, 0, 0, 1],
            [1, 1, 1, 1, 1],
        ]
        top_bar = [
            [1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ]
        diag_slash = [
            [1, 0, 0, 0, 0],
            [0, 1, 0, 0, 0],
            [0, 0, 1, 0, 0],
            [0, 0, 0, 1, 0],
            [0, 0, 0, 0, 1],
        ]
        pairs = [
            (diamond, "A centered diamond crystal shape"),
            (border_box, "A hollow square frame border"),
            (top_bar, "A solid horizontal banner at the top"),
            (diag_slash, "A diagonal line from top-left to bottom-right"),
        ]
        self.fit(pairs)
        res = self.predict(custom_input or self.metadata.input_example)
        return {"training": self.training_metrics, "result": res.to_dict()}
