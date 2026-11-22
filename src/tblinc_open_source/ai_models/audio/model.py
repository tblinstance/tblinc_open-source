"""17. AudioSpectrumModel: Pure-Python DFT spectral analyzer & acoustic/speech classifier."""

from __future__ import annotations

import math
import time
from typing import Any

from ..core import BaseAIModel, ModelMetadata, PredictionResult, register_model, timed_predict


def _synth_wave(freq_hz: float, sample_rate: int = 1000, n_samples: int = 64, amp: float = 0.8) -> list[float]:
    return [amp * math.sin(2.0 * math.pi * freq_hz * i / sample_rate) for i in range(n_samples)]


def _dft_magnitudes(signal: list[float]) -> list[float]:
    n = len(signal)
    half = max(1, n // 2)
    mags: list[float] = []
    for k in range(half):
        re_acc = 0.0
        im_acc = 0.0
        for t, x in enumerate(signal):
            angle = 2.0 * math.pi * k * t / n
            re_acc += x * math.cos(angle)
            im_acc -= x * math.sin(angle)
        mags.append(math.sqrt(re_acc * re_acc + im_acc * im_acc) / max(1, n))
    return mags


@register_model
class AudioSpectrumModel(BaseAIModel):
    """Spectral feature extractor (DFT, centroid, ZCR, RMS, frequency bands) + softmax acoustic classifier."""

    metadata = ModelMetadata(
        key="audio",
        name="Sound & Speech Classifier",
        category="Audio / Speech",
        task="Acoustic & Frequency Band Classification",
        description="Computes DFT spectrum, spectral centroid, zero-crossing rate, and classifies 1D audio waveforms.",
        input_example={"freq_hz": 240, "sample_rate": 1000},
        tags=["audio", "asr", "dft", "signal-processing"],
    )

    def __init__(self, lr: float = 0.2, epochs: int = 140) -> None:
        super().__init__()
        self.lr = lr
        self.epochs = epochs
        self.classes: list[str] = []
        self.weights: list[list[float]] = []
        self.biases: list[float] = []

    def extract_features(self, signal: list[float], sample_rate: int = 1000) -> tuple[list[float], dict[str, float]]:
        xs = [float(v) for v in signal]
        n = max(1, len(xs))
        rms = math.sqrt(sum(v * v for v in xs) / n)
        zcr = sum(1 for i in range(1, len(xs)) if (xs[i - 1] >= 0) != (xs[i] >= 0)) / max(1, n - 1)
        mags = _dft_magnitudes(xs)
        tot_mag = sum(mags) or 1e-9
        bins = len(mags)
        centroid_bin = sum(i * m for i, m in enumerate(mags)) / tot_mag
        centroid_hz = centroid_bin * (sample_rate / max(1, len(xs)))
        peak_bin = max(range(bins), key=lambda i: mags[i])
        peak_hz = peak_bin * (sample_rate / max(1, len(xs)))

        b1 = max(1, bins // 3)
        b2 = max(b1 + 1, (2 * bins) // 3)
        low_e = sum(mags[:b1]) / tot_mag
        mid_e = sum(mags[b1:b2]) / tot_mag
        high_e = sum(mags[b2:]) / tot_mag

        feats = [rms, zcr, centroid_bin / max(1, bins), peak_bin / max(1, bins), low_e, mid_e, high_e]
        summary = {
            "rms": round(rms, 4),
            "zcr": round(zcr, 4),
            "spectral_centroid_hz": round(centroid_hz, 2),
            "dominant_freq_hz": round(peak_hz, 2),
        }
        return feats, summary

    def _softmax(self, logits: list[float]) -> list[float]:
        mx = max(logits)
        exps = [math.exp(v - mx) for v in logits]
        s = sum(exps) or 1.0
        return [e / s for e in exps]

    def fit(self, signals: list[list[float]], labels: list[str], sample_rate: int = 1000) -> AudioSpectrumModel:
        if not signals or len(signals) != len(labels):
            raise ValueError("signals and labels must be non-empty and match in length.")
        X = [self.extract_features(sig, sample_rate=sample_rate)[0] for sig in signals]
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
        acc = self.evaluate(signals, labels, sample_rate=sample_rate)["accuracy"]
        self.training_metrics = {"classes": self.classes, "train_accuracy": acc, "samples": n}
        return self

    @timed_predict
    def predict(self, data: list[float] | dict[str, Any]) -> PredictionResult:
        if not self.is_fitted:
            raise RuntimeError("AudioSpectrumModel must be fitted before predict().")
        sample_rate = 1000
        if isinstance(data, dict):
            sample_rate = int(data.get("sample_rate", 1000))
            if "waveform" in data:
                signal = [float(v) for v in data["waveform"]]
            else:
                freq = float(data.get("freq_hz", 200.0))
                signal = _synth_wave(freq, sample_rate=sample_rate)
        else:
            signal = [float(v) for v in data]

        feats, summary = self.extract_features(signal, sample_rate=sample_rate)
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
            details={"probabilities": {c: round(p, 4) for c, p in zip(self.classes, probs)}, "spectrum": summary},
        )

    def evaluate(self, signals: list[list[float]], labels: list[str], sample_rate: int = 1000) -> dict[str, Any]:
        correct = sum(
            1 for s, y in zip(signals, labels) if self.predict({"waveform": s, "sample_rate": sample_rate}).prediction == y
        )
        return {"accuracy": round(correct / max(1, len(labels)), 4), "samples": len(labels)}

    def get_state(self) -> dict[str, Any]:
        return {"lr": self.lr, "epochs": self.epochs, "classes": self.classes, "weights": self.weights, "biases": self.biases}

    def set_state(self, state: dict[str, Any]) -> None:
        self.lr = float(state["lr"])
        self.epochs = int(state["epochs"])
        self.classes = list(state["classes"])
        self.weights = state["weights"]
        self.biases = list(state["biases"])

    def _run_demo(self, custom_input: Any = None) -> dict[str, Any]:
        signals = [
            _synth_wave(60), _synth_wave(80), _synth_wave(100),
            _synth_wave(220), _synth_wave(250), _synth_wave(280),
            _synth_wave(380), _synth_wave(410), _synth_wave(440),
        ]
        labels = [
            "bass_low", "bass_low", "bass_low",
            "voice_mid", "voice_mid", "voice_mid",
            "treble_high", "treble_high", "treble_high",
        ]
        self.fit(signals, labels)
        res = self.predict(custom_input or self.metadata.input_example)
        return {"training": self.training_metrics, "result": res.to_dict()}
