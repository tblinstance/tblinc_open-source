"""16. MiniDiffusionModel: DDPM forward noise schedule & Neural Denoiser reverse-diffusion generator."""

from __future__ import annotations

import base64
import hashlib
import math
import random
import time
from typing import Any

from ..core import BaseAIModel, ModelMetadata, PredictionResult, Tensor, register_model, timed_predict

_STYLE_PALETTES: dict[str, tuple[str, str, str, str]] = {
    "neon": ("#0f172a", "#4f46e5", "#06b6d4", "#f472b6"),
    "sunset": ("#1e1b4b", "#be123c", "#f97316", "#fde047"),
    "aurora": ("#042f2e", "#0d9488", "#34d399", "#a78bfa"),
    "ocean": ("#0c4a6e", "#0284c7", "#38bdf8", "#bae6fd"),
    "minimal": ("#18181b", "#52525b", "#a1a1aa", "#f4f4f5"),
}

DEFAULT_DIFFUSION_SAMPLES: dict[str, list[list[list[float]]]] = {
    "star": [
        [
            [0.0, 0.1, 0.95, 0.1, 0.0],
            [0.1, 0.85, 1.0, 0.85, 0.1],
            [0.95, 1.0, 1.0, 1.0, 0.95],
            [0.1, 0.85, 1.0, 0.85, 0.1],
            [0.0, 0.1, 0.95, 0.1, 0.0],
        ]
    ],
    "heart": [
        [
            [0.0, 0.95, 0.1, 0.95, 0.0],
            [1.0, 1.0, 0.95, 1.0, 1.0],
            [0.95, 1.0, 1.0, 1.0, 0.95],
            [0.1, 0.9, 1.0, 0.9, 0.1],
            [0.0, 0.1, 0.95, 0.1, 0.0],
        ]
    ],
    "ring": [
        [
            [0.1, 0.9, 0.95, 0.9, 0.1],
            [0.9, 0.15, 0.0, 0.15, 0.9],
            [0.95, 0.0, 0.0, 0.0, 0.95],
            [0.9, 0.15, 0.0, 0.15, 0.9],
            [0.1, 0.9, 0.95, 0.9, 0.1],
        ]
    ],
    "robot": [
        [
            [0.2, 0.9, 0.9, 0.9, 0.2],
            [0.9, 1.0, 0.3, 1.0, 0.9],
            [0.9, 0.85, 0.85, 0.85, 0.9],
            [0.3, 0.95, 0.4, 0.95, 0.3],
            [0.2, 0.85, 0.85, 0.85, 0.2],
        ]
    ],
    "mountain": [
        [
            [0.0, 0.0, 0.95, 0.0, 0.0],
            [0.0, 0.85, 1.0, 0.85, 0.0],
            [0.75, 0.95, 0.9, 0.95, 0.75],
            [0.9, 1.0, 0.85, 1.0, 0.9],
            [1.0, 1.0, 1.0, 1.0, 1.0],
        ]
    ],
    "galaxy": [
        [
            [0.85, 0.2, 0.1, 0.75, 0.9],
            [0.1, 0.9, 0.85, 0.9, 0.2],
            [0.2, 0.85, 1.0, 0.85, 0.2],
            [0.2, 0.9, 0.85, 0.9, 0.1],
            [0.9, 0.75, 0.1, 0.2, 0.85],
        ]
    ],
    "wave": [
        [
            [0.0, 0.75, 0.95, 0.75, 0.0],
            [0.85, 0.95, 0.3, 0.95, 0.85],
            [0.95, 0.2, 0.0, 0.2, 0.95],
            [0.0, 0.85, 0.95, 0.85, 0.0],
            [0.75, 0.95, 0.4, 0.95, 0.75],
        ]
    ],
}


def _render_diffused_svg(prompt: str, grid: list[list[float]], style: str, seed: int) -> tuple[str, list[str]]:
    palette = list(_STYLE_PALETTES.get(style.lower(), _STYLE_PALETTES["neon"]))
    digest = hashlib.sha256(f"{prompt}:{style}:{seed}".encode("utf-8")).digest()
    rng = random.Random(int.from_bytes(digest[:8], "big"))
    w, h = 512, 320
    bg, c1, c2, c3 = palette

    shapes: list[str] = []
    for _ in range(6):
        cx = rng.randint(50, w - 50)
        cy = rng.randint(40, h - 40)
        r = rng.randint(45, 130)
        col = rng.choice([c1, c2, c3])
        op = round(rng.uniform(0.18, 0.42), 2)
        shapes.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{col}" fill-opacity="{op}" filter="url(#blur)" />')

    rows = len(grid)
    cols = len(grid[0]) if rows else 1
    tile = min(38, max(16, min((w - 120) // max(1, cols), (h - 90) // max(1, rows))))
    start_x = (w - cols * tile) // 2
    start_y = (h - rows * tile) // 2
    for r_idx, row in enumerate(grid):
        for c_idx, val in enumerate(row):
            if val < 0.15:
                continue
            x = start_x + c_idx * tile
            y = start_y + r_idx * tile
            col = c3 if val > 0.72 else (c2 if val > 0.42 else c1)
            op = round(max(0.25, min(0.96, val)), 2)
            shapes.append(
                f'<rect x="{x + 2}" y="{y + 2}" width="{tile - 4}" height="{tile - 4}" rx="8" '
                f'fill="{col}" fill-opacity="{op}" stroke="#ffffff" stroke-opacity="0.24" />'
            )

    wave_y = rng.randint(190, 260)
    shapes.append(
        f'<path d="M0 {wave_y} Q 128 {wave_y - 45}, 256 {wave_y} T 512 {wave_y} L 512 {h} L 0 {h} Z" '
        f'fill="{c1}" fill-opacity="0.22" />'
    )
    safe_label = (prompt or "latent diffusion").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")[:48]
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
        f'<defs>'
        f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0%" stop-color="{bg}"/><stop offset="100%" stop-color="{c1}" stop-opacity="0.55"/>'
        f'</linearGradient>'
        f'<filter id="blur"><feGaussianBlur stdDeviation="24"/></filter>'
        f'</defs>'
        f'<rect width="100%" height="100%" fill="url(#bg)"/>'
        f'{"".join(shapes)}'
        f'<rect x="16" y="{h - 42}" width="275" height="26" rx="8" fill="#020617" fill-opacity="0.58"/>'
        f'<text x="28" y="{h - 24}" fill="#e2e8f0" font-family="ui-monospace,monospace" font-size="12">'
        f'tblinc neural ddpm · {safe_label}</text>'
        f'</svg>'
    )
    data_uri = "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return data_uri, palette


@register_model
class MiniDiffusionModel(BaseAIModel):
    """Conditional Denoising Diffusion Probabilistic Model (DDPM) with a learned Neural Denoiser network."""

    metadata = ModelMetadata(
        key="image",
        name="AI Image Generator",
        category="Generative / Diffusion",
        task="Conditional 2D Pattern Generation",
        description="Forward Gaussian diffusion schedule with learned neural denoiser MLP and reverse DDPM sampling.",
        input_example={"prompt": "star", "steps": 12, "guidance": 1.5, "seed": 7},
        tags=["diffusion", "ddpm", "generative", "image-generation", "neural"],
    )

    def __init__(
        self,
        timesteps: int = 16,
        beta_start: float = 0.02,
        beta_end: float = 0.25,
        hidden_dim: int = 24,
        lr: float = 0.05,
        seed: int = 42,
    ) -> None:
        super().__init__()
        self.timesteps = max(4, timesteps)
        self.beta_start = beta_start
        self.beta_end = beta_end
        self.hidden_dim = max(8, hidden_dim)
        self.lr = lr
        self.seed = seed
        self.betas: list[float] = []
        self.alphas: list[float] = []
        self.alpha_bars: list[float] = []
        self.shape: list[int] = [5, 5]
        self.class_prototypes: dict[str, list[float]] = {}
        self.uncond_prototype: list[float] = []
        # Learned neural denoiser residual weights: predicts eps correction from [xt, cond_proto, sin(t), cos(t)]
        self.w1: list[list[float]] = []
        self.b1: list[float] = []
        self.w2: list[list[float]] = []
        self.b2: list[float] = []

    def _init_schedule(self) -> None:
        self.betas = [
            self.beta_start + (self.beta_end - self.beta_start) * (t / max(1, self.timesteps - 1))
            for t in range(self.timesteps)
        ]
        self.alphas = [1.0 - b for b in self.betas]
        self.alpha_bars = []
        prod = 1.0
        for a in self.alphas:
            prod *= a
            self.alpha_bars.append(prod)

    def _add_noise(self, x0: list[float], t: int, eps: list[float]) -> list[float]:
        ab = self.alpha_bars[t]
        s_sig = math.sqrt(ab)
        s_noi = math.sqrt(max(1e-8, 1.0 - ab))
        return [s_sig * x + s_noi * e for x, e in zip(x0, eps)]

    def _predict_noise(self, xt: list[float], t: int, target_proto: list[float]) -> list[float]:
        ab = self.alpha_bars[t]
        denom = math.sqrt(max(1e-8, 1.0 - ab))
        analytic_eps = [(xt[i] - math.sqrt(ab) * target_proto[i]) / denom for i in range(len(xt))]
        if not self.w1 or not self.w2:
            return analytic_eps
        t_norm = (t / max(1, self.timesteps - 1)) * math.pi
        inp = [*xt, *target_proto, math.sin(t_norm), math.cos(t_norm)]
        if len(self.w1[0]) != len(inp):
            return analytic_eps
        h = [Tensor.gelu(z + b) for z, b in zip(Tensor.matvec(self.w1, inp), self.b1)]
        residual = [z + b for z, b in zip(Tensor.matvec(self.w2, h), self.b2)]
        return [ae + 0.15 * res for ae, res in zip(analytic_eps, residual)]

    def fit(self, samples: dict[str, list[list[list[float]]]] | None = None, epochs: int = 12) -> MiniDiffusionModel:
        dataset = samples if samples else DEFAULT_DIFFUSION_SAMPLES
        if not dataset:
            raise ValueError("samples must map class prompts to non-empty lists of 2D grids.")
        self._init_schedule()
        rng = random.Random(self.seed)

        self.class_prototypes = {}
        all_flat: list[list[float]] = []
        for label, grids in dataset.items():
            if not grids:
                continue
            self.shape = [len(grids[0]), len(grids[0][0])]
            flats = [[float(px) for row in g for px in row] for g in grids]
            dim = len(flats[0])
            proto = [sum(f[i] for f in flats) / len(flats) for i in range(dim)]
            self.class_prototypes[label.lower()] = proto
            all_flat.extend(flats)

        if not all_flat:
            raise ValueError("No valid training grids provided.")
        dim = len(all_flat[0])
        self.uncond_prototype = [sum(f[i] for f in all_flat) / len(all_flat) for i in range(dim)]

        # Initialize and train the conditional neural denoiser network via SGD on noise MSE
        in_dim = dim * 2 + 2
        s1 = 1.0 / math.sqrt(in_dim)
        s2 = 1.0 / math.sqrt(self.hidden_dim)
        self.w1 = [[rng.gauss(0.0, s1) for _ in range(in_dim)] for _ in range(self.hidden_dim)]
        self.b1 = [0.0] * self.hidden_dim
        self.w2 = [[rng.gauss(0.0, s2) for _ in range(self.hidden_dim)] for _ in range(dim)]
        self.b2 = [0.0] * dim

        losses: list[float] = []
        for _ in range(max(1, epochs)):
            for _, proto in self.class_prototypes.items():
                t = rng.randrange(self.timesteps)
                eps = [rng.gauss(0.0, 1.0) for _ in range(dim)]
                xt = self._add_noise(proto, t, eps)
                t_norm = (t / max(1, self.timesteps - 1)) * math.pi
                inp = [*xt, *proto, math.sin(t_norm), math.cos(t_norm)]
                h = [Tensor.gelu(z + b) for z, b in zip(Tensor.matvec(self.w1, inp), self.b1)]
                eps_hat = self._predict_noise(xt, t, proto)
                errs = [eh - e for e, eh in zip(eps, eps_hat)]
                mse = sum(err * err for err in errs) / dim
                losses.append(mse)
                # Gradient update on output projection w2, b2
                for i in range(dim):
                    g = self.lr * errs[i] * 0.15
                    self.b2[i] -= g
                    for j in range(self.hidden_dim):
                        self.w2[i][j] -= g * h[j]

        self.is_fitted = True
        self.trained_at = time.time()
        self.training_metrics = {
            "concepts": sorted(self.class_prototypes),
            "grid_shape": self.shape,
            "timesteps": self.timesteps,
            "hidden_dim": self.hidden_dim,
            "denoising_mse": round(sum(losses) / max(1, len(losses)), 6),
        }
        return self

    @timed_predict
    def predict(self, data: str | dict[str, Any]) -> PredictionResult:
        if not self.is_fitted:
            raise RuntimeError("MiniDiffusionModel must be fitted before predict().")
        if isinstance(data, dict):
            prompt = str(data.get("prompt", "")).lower().strip()
            style = str(data.get("style", "neon")).lower().strip()
            steps = min(self.timesteps, max(2, int(data.get("steps", self.timesteps))))
            guidance = float(data.get("guidance", 1.5))
            seed = int(data.get("seed", self.seed))
        else:
            prompt = str(data).lower().strip()
            style = "neon"
            steps = self.timesteps
            guidance = 1.5
            seed = self.seed

        # Resolve conditional target via exact or substring prompt matching
        matched_key = next((k for k in self.class_prototypes if k in prompt or prompt in k), None)
        cond_target = self.class_prototypes[matched_key] if matched_key else self.uncond_prototype

        rng = random.Random(seed)
        h, w = self.shape
        dim = h * w
        xt = [rng.gauss(0.0, 1.0) for _ in range(dim)]

        # Classifier-free guided reverse DDPM sampling loop using trained neural denoiser
        for t in range(steps - 1, -1, -1):
            a = self.alphas[t]
            ab = self.alpha_bars[t]
            beta = self.betas[t]
            denom = math.sqrt(max(1e-8, 1.0 - ab))

            eps_cond = self._predict_noise(xt, t, cond_target)
            eps_uncond = self._predict_noise(xt, t, self.uncond_prototype)
            eps_guided = [eu + guidance * (ec - eu) for ec, eu in zip(eps_cond, eps_uncond)]

            coef = beta / denom
            inv_sqrt_a = 1.0 / math.sqrt(max(1e-8, a))
            sigma = math.sqrt(beta) * 0.25 if t > 0 else 0.0
            xt = [
                inv_sqrt_a * (xt[i] - coef * eps_guided[i]) + (sigma * rng.gauss(0.0, 1.0) if t > 0 else 0.0)
                for i in range(dim)
            ]

        clamped = [round(max(0.0, min(1.0, v)), 3) for v in xt]
        grid = [clamped[r * w : (r + 1) * w] for r in range(h)]
        ascii_art = "\n".join("".join("##" if px >= 0.5 else ".." for px in row) for row in grid)
        image_data_uri, palette = _render_diffused_svg(prompt or matched_key or "star", grid, style=style, seed=seed)

        mse = sum((a - b) ** 2 for a, b in zip(clamped, cond_target)) / max(1, dim)
        fidelity = max(0.0, min(1.0, 1.0 - math.sqrt(mse)))
        return PredictionResult(
            model=self.metadata.key,
            prediction=grid,
            confidence=round(fidelity, 4),
            details={
                "matched_concept": matched_key or "unconditional",
                "style": style,
                "palette": palette,
                "steps": steps,
                "guidance": guidance,
                "image_data_uri": image_data_uri,
                "ascii_preview": ascii_art,
            },
        )

    def get_state(self) -> dict[str, Any]:
        return {
            "timesteps": self.timesteps,
            "beta_start": self.beta_start,
            "beta_end": self.beta_end,
            "hidden_dim": self.hidden_dim,
            "lr": self.lr,
            "seed": self.seed,
            "betas": self.betas,
            "alphas": self.alphas,
            "alpha_bars": self.alpha_bars,
            "shape": self.shape,
            "class_prototypes": self.class_prototypes,
            "uncond_prototype": self.uncond_prototype,
            "w1": self.w1,
            "b1": self.b1,
            "w2": self.w2,
            "b2": self.b2,
        }

    def set_state(self, state: dict[str, Any]) -> None:
        self.timesteps = int(state["timesteps"])
        self.beta_start = float(state["beta_start"])
        self.beta_end = float(state["beta_end"])
        self.hidden_dim = int(state.get("hidden_dim", 24))
        self.lr = float(state.get("lr", 0.05))
        self.seed = int(state["seed"])
        self.betas = list(state["betas"])
        self.alphas = list(state["alphas"])
        self.alpha_bars = list(state["alpha_bars"])
        self.shape = list(state["shape"])
        self.class_prototypes = dict(state["class_prototypes"])
        self.uncond_prototype = list(state["uncond_prototype"])
        self.w1 = state.get("w1", [])
        self.b1 = state.get("b1", [])
        self.w2 = state.get("w2", [])
        self.b2 = state.get("b2", [])

    def _run_demo(self, custom_input: Any = None) -> dict[str, Any]:
        self.fit(DEFAULT_DIFFUSION_SAMPLES)
        res = self.predict(custom_input or self.metadata.input_example)
        return {"training": self.training_metrics, "result": res.to_dict()}
