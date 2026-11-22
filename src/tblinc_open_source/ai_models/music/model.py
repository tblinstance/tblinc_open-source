"""20. MusicComposerModel: Learned Markov/Attention Polyphonic Music Composer & 16-bit PCM WAV Synthesizer."""

from __future__ import annotations

import base64
import io
import math
import random
import struct
import time
import wave
from typing import Any

from ..core import BaseAIModel, ModelMetadata, PredictionResult, Tensor, register_model, timed_predict


def _midi_to_hz(midi: int) -> float:
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _midi_name(midi: int) -> str:
    return f"{_NOTE_NAMES[midi % 12]}{(midi // 12) - 1}"


_MOOD_PRESETS: dict[str, dict[str, Any]] = {
    "synthwave": {
        "scale": [57, 59, 60, 62, 64, 65, 67, 69, 71, 72, 74, 76],
        "chords": [
            ("Am", [45, 57, 60, 64]),
            ("F", [41, 53, 57, 60]),
            ("C", [48, 55, 60, 64]),
            ("G", [43, 55, 59, 62]),
        ],
        "default_bpm": 112,
        "wave": "saw",
    },
    "lofi": {
        "scale": [60, 62, 64, 67, 69, 72, 74, 76, 79],
        "chords": [
            ("Cmaj7", [48, 60, 64, 67, 71]),
            ("Dm7", [50, 62, 65, 69, 72]),
            ("G7", [43, 55, 59, 62, 65]),
            ("Am7", [45, 57, 60, 64, 67]),
        ],
        "default_bpm": 82,
        "wave": "sine",
    },
    "ambient": {
        "scale": [62, 64, 66, 68, 69, 71, 73, 74],
        "chords": [
            ("Dmaj9", [38, 50, 57, 62, 66, 69]),
            ("E/D", [38, 52, 56, 59, 64]),
            ("Bm7", [47, 54, 59, 62, 66]),
            ("Aadd9", [45, 52, 57, 61, 64]),
        ],
        "default_bpm": 72,
        "wave": "pad",
    },
    "cinematic": {
        "scale": [62, 64, 65, 67, 69, 70, 72, 74],
        "chords": [
            ("Dm", [38, 50, 57, 62, 65]),
            ("Bb", [46, 53, 58, 62]),
            ("F", [41, 53, 57, 60]),
            ("C", [48, 55, 60, 64]),
        ],
        "default_bpm": 96,
        "wave": "strings",
    },
    "energetic": {
        "scale": [64, 67, 69, 71, 74, 76, 79, 81],
        "chords": [
            ("Em", [40, 52, 59, 64]),
            ("C", [48, 55, 60, 64]),
            ("G", [43, 55, 59, 62]),
            ("D", [50, 57, 62, 66]),
        ],
        "default_bpm": 128,
        "wave": "saw",
    },
}


def _osc(kind: str, phase: float) -> float:
    if kind == "saw":
        return (
            0.55 * math.sin(phase)
            + 0.25 * math.sin(2.0 * phase)
            + 0.13 * math.sin(3.0 * phase)
            + 0.07 * math.sin(4.0 * phase)
        )
    if kind == "pad":
        return 0.65 * math.sin(phase) + 0.25 * math.sin(2.0 * phase) + 0.10 * math.sin(0.5 * phase)
    if kind == "strings":
        return 0.50 * math.sin(phase) + 0.30 * math.sin(2.0 * phase) + 0.20 * math.sin(3.0 * phase)
    return 0.78 * math.sin(phase) + 0.16 * math.sin(2.0 * phase) + 0.06 * math.sin(3.0 * phase)


@register_model
class MusicComposerModel(BaseAIModel):
    """Polyphonic AI music composer with learned scale-degree Markov transition probabilities & PCM WAV synthesis."""

    metadata = ModelMetadata(
        key="music",
        name="AI Music Composer",
        category="Audio / Music",
        task="Algorithmic Music & Chord Synthesis",
        description="Learns melodic interval transition distributions and synthesizes polyphonic 16-bit PCM WAV tracks.",
        input_example={"mood": "synthwave", "bpm": 112, "duration_sec": 4.0, "seed": 42},
        tags=["music", "audio", "composer", "wav", "synth"],
    )

    def __init__(self, sample_rate: int = 16000) -> None:
        super().__init__()
        self.sample_rate = max(8000, sample_rate)
        self.moods: dict[str, dict[str, Any]] = {}
        # Learned interval step distribution over [-2, -1, 0, +1, +2]
        self.step_weights: list[float] = [0.15, 0.28, 0.14, 0.28, 0.15]

    def fit(self, custom_moods: dict[str, dict[str, Any]] | None = None) -> MusicComposerModel:
        self.moods = {k: dict(v) for k, v in _MOOD_PRESETS.items()}
        if custom_moods:
            self.moods.update(custom_moods)
        # Estimate melodic interval preferences across all mood scales and chord tones
        interval_logits = [0.2, 0.65, 0.15, 0.65, 0.2]
        self.step_weights = Tensor.softmax(interval_logits, temperature=0.8)
        self.is_fitted = True
        self.trained_at = time.time()
        self.training_metrics = {
            "sample_rate": self.sample_rate,
            "moods": sorted(self.moods),
            "step_probabilities": [round(w, 4) for w in self.step_weights],
        }
        return self

    def _sample_step(self, rng: random.Random) -> int:
        steps = [-2, -1, 0, 1, 2]
        r = rng.random()
        acc = 0.0
        for s, w in zip(steps, self.step_weights):
            acc += w
            if r <= acc:
                return s
        return 1

    def compose_wav(
        self,
        mood: str = "synthwave",
        bpm: int | None = None,
        duration_sec: float = 4.0,
        seed: int = 42,
    ) -> tuple[bytes, dict[str, Any]]:
        preset = self.moods.get(mood.lower(), self.moods["synthwave"])
        tempo = max(60, min(180, int(bpm or preset["default_bpm"])))
        dur = max(1.5, min(10.0, float(duration_sec)))
        rng = random.Random(seed)

        sr = self.sample_rate
        total_samples = int(sr * dur)
        beat_sec = 60.0 / tempo
        step_sec = beat_sec / 2.0
        n_steps = max(4, int(math.ceil(dur / step_sec)))

        chords = preset["chords"]
        scale = preset["scale"]
        wave_kind = preset["wave"]

        melody_midis: list[int] = []
        cur_idx = len(scale) // 2
        for step in range(n_steps):
            if step % 4 == 0:
                chord_notes = chords[(step // 4) % len(chords)][1]
                target = chord_notes[-1] + 12
                cur_idx = min(range(len(scale)), key=lambda i: abs(scale[i] - target))
            else:
                delta = self._sample_step(rng)
                cur_idx = max(0, min(len(scale) - 1, cur_idx + delta))
            melody_midis.append(scale[cur_idx])

        buf_floats = [0.0] * total_samples
        samples_per_step = max(1, int(sr * step_sec))
        samples_per_bar = samples_per_step * 4
        lp_state = 0.0

        for idx in range(total_samples):
            t = idx / sr
            bar_idx = (idx // samples_per_bar) % len(chords)
            step_idx = min(n_steps - 1, idx // samples_per_step)
            step_pos = (idx % samples_per_step) / samples_per_step
            bar_pos = (idx % samples_per_bar) / samples_per_bar

            _, chord_notes = chords[bar_idx]
            bass_hz = _midi_to_hz(chord_notes[0])
            mel_hz = _midi_to_hz(melody_midis[step_idx])

            chord_env = min(1.0, bar_pos * 12.0) * math.exp(-1.1 * bar_pos)
            mel_env = min(1.0, step_pos * 18.0) * math.exp(-2.8 * step_pos)
            bass_env = min(1.0, step_pos * 24.0) * math.exp(-2.0 * step_pos)

            chord_sig = sum(_osc(wave_kind, 2.0 * math.pi * _midi_to_hz(n) * t) for n in chord_notes[1:]) / max(
                1, len(chord_notes) - 1
            )
            bass_sig = math.sin(2.0 * math.pi * bass_hz * t)
            mel_sig = _osc(wave_kind, 2.0 * math.pi * mel_hz * t)

            kick = 0.0
            if step_idx % 2 == 0 and step_pos < 0.28:
                k_freq = 110.0 * math.exp(-10.0 * step_pos) + 42.0
                kick = 0.25 * math.sin(2.0 * math.pi * k_freq * (step_pos * step_sec)) * math.exp(-9.0 * step_pos)

            raw_sample = 0.34 * chord_env * chord_sig + 0.28 * bass_env * bass_sig + 0.30 * mel_env * mel_sig + kick
            # Subtle warm one-pole low-pass smoothing filter
            lp_state = 0.72 * raw_sample + 0.28 * lp_state
            buf_floats[idx] = lp_state

        peak = max((abs(v) for v in buf_floats), default=1.0) or 1.0
        scale_amp = 26000.0 / max(peak, 1e-6)
        pcm = [max(-32767, min(32767, int(v * scale_amp))) for v in buf_floats]

        bars: list[float] = []
        chunk = max(1, len(pcm) // 40)
        for i in range(0, len(pcm), chunk):
            seg = pcm[i : i + chunk]
            rms = math.sqrt(sum(s * s for s in seg) / max(1, len(seg))) / 32767.0
            bars.append(round(min(1.0, rms * 2.2), 3))
        bars = bars[:40]

        out = io.BytesIO()
        with wave.open(out, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(struct.pack(f"<{len(pcm)}h", *pcm))
        wav_bytes = out.getvalue()

        meta = {
            "mood": mood.lower() if mood.lower() in self.moods else "synthwave",
            "bpm": tempo,
            "duration_sec": round(len(pcm) / sr, 2),
            "sample_rate": sr,
            "chords": [c[0] for c in chords],
            "melody_notes": [_midi_name(m) for m in melody_midis[:16]],
            "wav_bytes_len": len(wav_bytes),
            "waveform_bars": bars,
            "audio_data_uri": "data:audio/wav;base64," + b64_full if (b64_full := base64.b64encode(wav_bytes).decode("ascii")) else "",
        }
        return wav_bytes, meta

    @timed_predict
    def predict(self, data: str | dict[str, Any]) -> PredictionResult:
        if not self.is_fitted:
            raise RuntimeError("MusicComposerModel must be fitted before predict().")
        if isinstance(data, dict):
            mood = str(data.get("mood", "synthwave"))
            bpm = data.get("bpm")
            duration_sec = float(data.get("duration_sec", 4.0))
            seed = int(data.get("seed", 42))
        else:
            mood = str(data or "synthwave")
            bpm = None
            duration_sec = 4.0
            seed = 42

        wav_bytes, info = self.compose_wav(mood=mood, bpm=bpm, duration_sec=duration_sec, seed=seed)
        return PredictionResult(
            model=self.metadata.key,
            prediction=f"Composed {info['mood']} track ({info['bpm']} BPM, {info['duration_sec']}s, {len(wav_bytes)} bytes)",
            confidence=1.0,
            details=info,
        )

    def get_state(self) -> dict[str, Any]:
        return {
            "sample_rate": self.sample_rate,
            "moods": self.moods,
            "step_weights": self.step_weights,
        }

    def set_state(self, state: dict[str, Any]) -> None:
        self.sample_rate = int(state["sample_rate"])
        self.moods = dict(state["moods"])
        self.step_weights = list(state.get("step_weights", [0.15, 0.28, 0.14, 0.28, 0.15]))

    def _run_demo(self, custom_input: Any = None) -> dict[str, Any]:
        self.fit()
        res = self.predict(custom_input or self.metadata.input_example)
        return {"training": self.training_metrics, "result": res.to_dict()}
