"""25. SpeechToTextModel: Pure-Python acoustic energy/ZCR frame-to-word speech transcriber (ASR)."""

from __future__ import annotations

import math
import time
from typing import Any

from ..core import BaseAIModel, ModelMetadata, PredictionResult, register_model, timed_predict


def _frame_features(frame: list[float]) -> tuple[float, float, float]:
    n = max(1, len(frame))
    rms = math.sqrt(sum(s * s for s in frame) / n)
    zcr = sum(1 for i in range(1, n) if (frame[i - 1] >= 0) != (frame[i] >= 0)) / max(1, n - 1)
    peak = max((abs(s) for s in frame), default=0.0)
    return rms, zcr, peak


@register_model
class SpeechToTextModel(BaseAIModel):
    """Acoustic feature-based ASR decoder mapping frame energy/ZCR profiles to spoken words."""

    metadata = ModelMetadata(
        key="transcribe",
        name="Speech-to-Text AI",
        category="Audio / Speech",
        task="Automatic Speech Recognition (ASR)",
        description="Decodes segmented audio waveform frames into transcribed text commands using RMS & zero-crossing profiles.",
        input_example={
            "frames": [
                [0.2, 0.5, 0.2, -0.4, -0.5, -0.2, 0.3, 0.5],
                [0.8, -0.8, 0.7, -0.7, 0.8, -0.8, 0.7, -0.7],
            ]
        },
        tags=["asr", "speech-to-text", "whisper", "audio"],
    )

    def __init__(self) -> None:
        super().__init__()
        self.lexicon: dict[str, list[float]] = {}

    def fit(self, lexicon: dict[str, list[float]] | None = None) -> SpeechToTextModel:
        if lexicon:
            self.lexicon = {str(word): [float(v) for v in feat] for word, feat in lexicon.items()}
        else:
            # Acoustic profile per token: [rms, zcr, peak]
            self.lexicon = {
                "hello": [0.38, 0.28, 0.52],
                "tblinc": [0.75, 0.95, 0.82],
                "start": [0.55, 0.55, 0.70],
                "stop": [0.22, 0.15, 0.30],
                "train": [0.65, 0.70, 0.85],
                "silence": [0.02, 0.05, 0.04],
            }
        self.is_fitted = True
        self.trained_at = time.time()
        self.training_metrics = {"vocabulary": sorted(self.lexicon), "vocab_size": len(self.lexicon)}
        return self

    def _decode_frame(self, frame: list[float]) -> tuple[str, float]:
        feat = _frame_features(frame)
        best_word = "silence"
        best_dist = float("inf")
        for word, proto in self.lexicon.items():
            d = math.sqrt(sum((a - b) ** 2 for a, b in zip(feat, proto)))
            if d < best_dist:
                best_dist = d
                best_word = word
        return best_word, round(1.0 / (1.0 + best_dist), 4)

    @timed_predict
    def predict(self, data: list[list[float]] | dict[str, Any]) -> PredictionResult:
        if not self.is_fitted:
            raise RuntimeError("SpeechToTextModel must be fitted before predict().")
        if isinstance(data, dict):
            if "frames" in data:
                frames = [[float(x) for x in f] for f in data["frames"]]
            elif "samples" in data:
                raw = [float(x) for x in data["samples"]]
                chunk = max(4, len(raw) // 2)
                frames = [raw[i : i + chunk] for i in range(0, len(raw), chunk) if raw[i : i + chunk]]
            else:
                frames = [[0.0] * 8]
        else:
            frames = [[float(x) for x in f] for f in data]

        words: list[str] = []
        confs: list[float] = []
        segments: list[dict[str, Any]] = []
        for idx, frame in enumerate(frames):
            w, conf = self._decode_frame(frame)
            segments.append({"segment": idx, "word": w, "confidence": conf})
            if w != "silence":
                words.append(w)
                confs.append(conf)

        transcript = " ".join(words)
        avg_conf = round(sum(confs) / max(1, len(confs)), 4) if confs else 0.0
        return PredictionResult(
            model=self.metadata.key,
            prediction=transcript,
            confidence=avg_conf,
            details={"segments": segments, "word_count": len(words)},
        )

    def get_state(self) -> dict[str, Any]:
        return {"lexicon": self.lexicon}

    def set_state(self, state: dict[str, Any]) -> None:
        self.lexicon = {str(k): [float(v) for v in vec] for k, vec in state["lexicon"].items()}

    def _run_demo(self, custom_input: Any = None) -> dict[str, Any]:
        self.fit()
        res = self.predict(custom_input or self.metadata.input_example)
        return {"training": self.training_metrics, "result": res.to_dict()}
