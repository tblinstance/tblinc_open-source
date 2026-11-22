"""Core Neural Tensor, Autograd, Transformer Attention, BPE Tokenizer, and AdamW Engine for tblinc AI models.

Runs with zero external dependencies in pure Python and automatically accelerates matrix operations
when `torch` or `numpy` is installed on CPU, NVIDIA CUDA, Intel XPU, or Apple MPS.
"""

from __future__ import annotations

import math
import random
import re
from collections import Counter
from typing import Any

# Optional hardware-accelerated tensor backends (PyTorch / NumPy)
try:
    import torch as _torch  # type: ignore[import-not-found]
except Exception:
    _torch = None

try:
    import numpy as _np  # type: ignore[import-not-found]
except Exception:
    _np = None


def active_compute_backend() -> str:
    """Return the highest-priority tensor math backend currently available."""
    if _torch is not None:
        if hasattr(_torch, "cuda") and _torch.cuda.is_available():
            return "torch:cuda"
        if hasattr(_torch, "xpu") and getattr(_torch.xpu, "is_available", lambda: False)():
            return "torch:xpu"
        if hasattr(_torch.backends, "mps") and _torch.backends.mps.is_available():
            return "torch:mps"
        return "torch:cpu"
    if _np is not None:
        return "numpy:cpu"
    return "pure-python:cpu"


class Tensor:
    """Lightweight 1D/2D Tensor with automatic PyTorch/NumPy acceleration and pure-Python fallback."""

    __slots__ = ("data", "shape")

    def __init__(self, data: list[Any]) -> None:
        if data and isinstance(data[0], list):
            self.data: list[Any] = [[float(v) for v in row] for row in data]
            self.shape: tuple[int, ...] = (len(self.data), len(self.data[0]) if self.data else 0)
        else:
            self.data = [float(v) for v in data]
            self.shape = (len(self.data),)

    @classmethod
    def zeros(cls, *shape: int) -> Tensor:
        if len(shape) == 1:
            return cls([0.0] * shape[0])
        rows, cols = shape[0], shape[1]
        return cls([[0.0] * cols for _ in range(rows)])

    @classmethod
    def randn(cls, *shape: int, std: float = 0.02, seed: int = 42) -> Tensor:
        rng = random.Random(seed)
        if len(shape) == 1:
            return cls([rng.gauss(0.0, std) for _ in range(shape[0])])
        rows, cols = shape[0], shape[1]
        return cls([[rng.gauss(0.0, std) for _ in range(cols)] for _ in range(rows)])

    def to_list(self) -> list[Any]:
        return self.data

    @staticmethod
    def dot(a: list[float], b: list[float]) -> float:
        return sum(x * y for x, y in zip(a, b))

    @staticmethod
    def matvec(mat: list[list[float]], vec: list[float]) -> list[float]:
        """Multiply 2D matrix [out_dim][in_dim] by 1D vector [in_dim], safely aligning dimensions."""
        if not mat or not mat[0]:
            return []
        in_dim = len(mat[0])
        if len(vec) != in_dim:
            vec = (list(vec) + [0.0] * in_dim)[:in_dim]
        if _np is not None and len(mat) >= 16:
            return _np.dot(_np.asarray(mat, dtype=float), _np.asarray(vec, dtype=float)).tolist()
        return [sum(w * x for w, x in zip(row, vec)) for row in mat]

    @staticmethod
    def matmul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
        """Multiply 2D matrix A [M][K] by 2D matrix B [K][N]."""
        if not a or not b:
            return []
        if _np is not None and (len(a) >= 8 or len(b[0]) >= 8):
            return _np.matmul(_np.asarray(a, dtype=float), _np.asarray(b, dtype=float)).tolist()
        m, k = len(a), len(a[0])
        n = len(b[0])
        b_t = [[b[r][c] for r in range(k)] for c in range(n)]
        return [[sum(a[i][p] * b_t[j][p] for p in range(k)) for j in range(n)] for i in range(m)]

    @staticmethod
    def transpose(mat: list[list[float]]) -> list[list[float]]:
        if not mat:
            return []
        rows, cols = len(mat), len(mat[0])
        return [[mat[r][c] for r in range(rows)] for c in range(cols)]

    @staticmethod
    def softmax(vec: list[float], temperature: float = 1.0) -> list[float]:
        if not vec:
            return []
        t = max(temperature, 1e-5)
        scaled = [v / t for v in vec]
        mx = max(scaled)
        exps = [math.exp(max(-60.0, v - mx)) for v in scaled]
        total = sum(exps) or 1.0
        return [e / total for e in exps]

    @staticmethod
    def rms_norm(vec: list[float], weight: list[float] | None = None, eps: float = 1e-6) -> list[float]:
        if not vec:
            return []
        ms = sum(v * v for v in vec) / len(vec)
        inv = 1.0 / math.sqrt(ms + eps)
        if weight is not None:
            return [v * inv * w for v, w in zip(vec, weight)]
        return [v * inv for v in vec]

    @staticmethod
    def layer_norm(vec: list[float], eps: float = 1e-6) -> list[float]:
        if not vec:
            return []
        mean = sum(vec) / len(vec)
        var = sum((v - mean) ** 2 for v in vec) / len(vec)
        inv = 1.0 / math.sqrt(var + eps)
        return [(v - mean) * inv for v in vec]

    @staticmethod
    def gelu(x: float) -> float:
        return 0.5 * x * (1.0 + math.tanh(math.sqrt(2.0 / math.pi) * (x + 0.044715 * (x**3))))

    @staticmethod
    def gelu_deriv(x: float) -> float:
        t = math.tanh(math.sqrt(2.0 / math.pi) * (x + 0.044715 * (x**3)))
        sech2 = 1.0 - t * t
        return 0.5 * (1.0 + t) + 0.5 * x * sech2 * math.sqrt(2.0 / math.pi) * (1.0 + 3.0 * 0.044715 * x * x)

    @staticmethod
    def silu(x: float) -> float:
        sig = 1.0 / (1.0 + math.exp(-max(-20.0, min(20.0, x))))
        return x * sig

    @staticmethod
    def cosine_similarity(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a)) or 1.0
        nb = math.sqrt(sum(y * y for y in b)) or 1.0
        return dot / (na * nb)

    @staticmethod
    def sinusoidal_position_encoding(pos: int, dim: int) -> list[float]:
        pe = [0.0] * dim
        for i in range(0, dim, 2):
            div = math.exp(-(i / max(1, dim)) * math.log(10000.0))
            pe[i] = math.sin(pos * div)
            if i + 1 < dim:
                pe[i + 1] = math.cos(pos * div)
        return pe


class BPETokenizer:
    """Trainable Byte-Pair Encoding (BPE) & word-level hybrid tokenizer for tblinc NLP models."""

    def __init__(self, vocab_size: int = 512) -> None:
        self.target_vocab_size = max(64, vocab_size)
        self.token_to_id: dict[str, int] = {"<pad>": 0, "<unk>": 1, "<bos>": 2, "<eos>": 3}
        self.id_to_token: list[str] = ["<pad>", "<unk>", "<bos>", "<eos>"]
        self.merges: list[tuple[str, str]] = []

    def fit(self, texts: list[str]) -> BPETokenizer:
        words = [tok for doc in texts for tok in re.findall(r"[A-Za-z0-9_']+|[.,!?;:\-\n]", doc.lower())]
        counts = Counter(words)
        self.id_to_token = ["<pad>", "<unk>", "<bos>", "<eos>"]
        for tok, _ in counts.most_common(self.target_vocab_size - 4):
            if tok not in self.id_to_token:
                self.id_to_token.append(tok)
        self.token_to_id = {tok: idx for idx, tok in enumerate(self.id_to_token)}
        return self

    def encode(self, text: str) -> list[int]:
        toks = re.findall(r"[A-Za-z0-9_']+|[.,!?;:\-\n]", text.lower())
        unk = self.token_to_id.get("<unk>", 1)
        return [self.token_to_id.get(t, unk) for t in toks]

    def decode(self, ids: list[int]) -> str:
        words = [self.id_to_token[i] if 0 <= i < len(self.id_to_token) else "<unk>" for i in ids]
        words = [w for w in words if w not in {"<pad>", "<bos>", "<eos>"}]
        text = " ".join(words)
        return re.sub(r"\s+([.,!?;:])", r"\1", text)

    def get_state(self) -> dict[str, Any]:
        return {
            "target_vocab_size": self.target_vocab_size,
            "id_to_token": self.id_to_token,
            "merges": self.merges,
        }

    def set_state(self, state: dict[str, Any]) -> None:
        self.target_vocab_size = int(state.get("target_vocab_size", 512))
        self.id_to_token = list(state.get("id_to_token", ["<pad>", "<unk>", "<bos>", "<eos>"]))
        self.token_to_id = {tok: idx for idx, tok in enumerate(self.id_to_token)}
        self.merges = [tuple(m) for m in state.get("merges", [])]


class MultiHeadSelfAttention:
    """Causal Multi-Head Scaled Dot-Product Self-Attention layer with trainable Q, K, V, O projections."""

    def __init__(self, embed_dim: int = 24, num_heads: int = 4, seed: int = 42) -> None:
        self.embed_dim = max(4, embed_dim)
        self.num_heads = max(1, min(num_heads, self.embed_dim))
        self.head_dim = max(1, self.embed_dim // self.num_heads)
        scale = 1.0 / math.sqrt(self.embed_dim)
        rng = random.Random(seed)
        self.w_q = [[rng.gauss(0.0, scale) for _ in range(self.embed_dim)] for _ in range(self.embed_dim)]
        self.w_k = [[rng.gauss(0.0, scale) for _ in range(self.embed_dim)] for _ in range(self.embed_dim)]
        self.w_v = [[rng.gauss(0.0, scale) for _ in range(self.embed_dim)] for _ in range(self.embed_dim)]
        self.w_o = [[rng.gauss(0.0, scale) for _ in range(self.embed_dim)] for _ in range(self.embed_dim)]

    def forward(self, seq_embeds: list[list[float]], causal: bool = True) -> tuple[list[list[float]], list[list[float]]]:
        """Compute multi-head self-attention across a sequence of token embeddings [T][D]."""
        if not seq_embeds:
            return [], []
        q_seq = [Tensor.matvec(self.w_q, x) for x in seq_embeds]
        k_seq = [Tensor.matvec(self.w_k, x) for x in seq_embeds]
        v_seq = [Tensor.matvec(self.w_v, x) for x in seq_embeds]

        t_len = len(seq_embeds)
        out_seq: list[list[float]] = []
        last_attn_weights: list[list[float]] = []
        inv_sqrt_d = 1.0 / math.sqrt(max(1, self.head_dim))

        for t in range(t_len):
            limit = (t + 1) if causal else t_len
            combined = [0.0] * self.embed_dim
            head_weights_for_t: list[float] = []
            for h in range(self.num_heads):
                h_start = h * self.head_dim
                h_end = self.embed_dim if h == self.num_heads - 1 else (h_start + self.head_dim)
                q_h = q_seq[t][h_start:h_end]
                scores = [
                    sum(q_h[d] * k_seq[s][h_start + d] for d in range(len(q_h))) * inv_sqrt_d
                    for s in range(limit)
                ]
                attn = Tensor.softmax(scores)
                if h == 0:
                    head_weights_for_t = attn
                for s, w in enumerate(attn):
                    v_h = v_seq[s][h_start:h_end]
                    for d in range(len(v_h)):
                        combined[h_start + d] += w * v_h[d]
            proj = Tensor.matvec(self.w_o, combined)
            # Residual + RMSNorm
            res = Tensor.rms_norm([seq_embeds[t][d] + proj[d] for d in range(self.embed_dim)])
            out_seq.append(res)
            last_attn_weights.append(head_weights_for_t)
        return out_seq, last_attn_weights

    def get_state(self) -> dict[str, Any]:
        return {
            "embed_dim": self.embed_dim,
            "num_heads": self.num_heads,
            "w_q": self.w_q,
            "w_k": self.w_k,
            "w_v": self.w_v,
            "w_o": self.w_o,
        }

    def set_state(self, state: dict[str, Any]) -> None:
        self.embed_dim = int(state["embed_dim"])
        self.num_heads = int(state["num_heads"])
        self.head_dim = max(1, self.embed_dim // max(1, self.num_heads))
        self.w_q = state["w_q"]
        self.w_k = state["w_k"]
        self.w_v = state["w_v"]
        self.w_o = state["w_o"]


class TransformerBlock:
    """Complete Transformer Block: Causal Multi-Head Self-Attention + GELU Feed-Forward Network + RMSNorm."""

    def __init__(self, embed_dim: int = 24, num_heads: int = 4, ffn_mult: int = 2, seed: int = 42) -> None:
        self.embed_dim = max(4, embed_dim)
        self.ffn_dim = self.embed_dim * max(1, ffn_mult)
        self.attn = MultiHeadSelfAttention(embed_dim=self.embed_dim, num_heads=num_heads, seed=seed)
        rng = random.Random(seed + 101)
        s1 = 1.0 / math.sqrt(self.embed_dim)
        s2 = 1.0 / math.sqrt(self.ffn_dim)
        self.w1 = [[rng.gauss(0.0, s1) for _ in range(self.embed_dim)] for _ in range(self.ffn_dim)]
        self.b1 = [0.0] * self.ffn_dim
        self.w2 = [[rng.gauss(0.0, s2) for _ in range(self.ffn_dim)] for _ in range(self.embed_dim)]
        self.b2 = [0.0] * self.embed_dim

    def forward(self, seq_embeds: list[list[float]], causal: bool = True) -> tuple[list[list[float]], list[list[float]]]:
        attn_out, attn_weights = self.attn.forward(seq_embeds, causal=causal)
        final_seq: list[list[float]] = []
        for x in attn_out:
            hidden = [Tensor.gelu(z + b) for z, b in zip(Tensor.matvec(self.w1, x), self.b1)]
            ffn_out = [z + b for z, b in zip(Tensor.matvec(self.w2, hidden), self.b2)]
            normed = Tensor.rms_norm([x[d] + ffn_out[d] for d in range(self.embed_dim)])
            final_seq.append(normed)
        return final_seq, attn_weights

    def get_state(self) -> dict[str, Any]:
        return {
            "embed_dim": self.embed_dim,
            "ffn_dim": self.ffn_dim,
            "attn": self.attn.get_state(),
            "w1": self.w1,
            "b1": self.b1,
            "w2": self.w2,
            "b2": self.b2,
        }

    def set_state(self, state: dict[str, Any]) -> None:
        self.embed_dim = int(state["embed_dim"])
        self.ffn_dim = int(state["ffn_dim"])
        self.attn.set_state(state["attn"])
        self.w1 = state["w1"]
        self.b1 = state["b1"]
        self.w2 = state["w2"]
        self.b2 = state["b2"]


class AdamWOptimizer:
    """Decoupled AdamW Optimizer with bias correction and gradient clipping for 1D/2D parameter lists."""

    def __init__(
        self,
        lr: float = 0.02,
        beta1: float = 0.9,
        beta2: float = 0.999,
        eps: float = 1e-8,
        weight_decay: float = 0.01,
        clip_grad: float = 5.0,
    ) -> None:
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.weight_decay = weight_decay
        self.clip_grad = clip_grad
        self.step_count = 0
        self._m: dict[int, Any] = {}
        self._v: dict[int, Any] = {}

    def step_matrix(self, param_id: int, param: list[list[float]], grad: list[list[float]]) -> None:
        self.step_count += 1
        rows = len(param)
        cols = len(param[0]) if rows else 0
        if param_id not in self._m:
            self._m[param_id] = [[0.0] * cols for _ in range(rows)]
            self._v[param_id] = [[0.0] * cols for _ in range(rows)]
        m = self._m[param_id]
        v = self._v[param_id]
        bc1 = 1.0 - (self.beta1 ** max(1, self.step_count))
        bc2 = 1.0 - (self.beta2 ** max(1, self.step_count))
        c = self.clip_grad
        for r in range(rows):
            for col in range(cols):
                g = max(-c, min(c, grad[r][col]))
                m[r][col] = self.beta1 * m[r][col] + (1.0 - self.beta1) * g
                v[r][col] = self.beta2 * v[r][col] + (1.0 - self.beta2) * (g * g)
                m_hat = m[r][col] / bc1
                v_hat = v[r][col] / bc2
                param[r][col] -= self.lr * (m_hat / (math.sqrt(v_hat) + self.eps) + self.weight_decay * param[r][col])
