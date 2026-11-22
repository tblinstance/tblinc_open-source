"""18. FormantTTSSynthesizer: Coarticulated Grapheme-to-Phoneme (G2P) Formant Text-to-Speech WAV synthesizer."""

from __future__ import annotations

import base64
import io
import math
import random
import struct
import time
import wave
from typing import Any

from ..core import BaseAIModel, ModelMetadata, PredictionResult, register_model, timed_predict

# Vocal-tract formant frequencies (F1, F2, F3 in Hz) and consonant noise ratio
_PHONEME_FORMANTS: dict[str, tuple[float, float, float, float]] = {
    "a": (730.0, 1090.0, 2440.0, 0.02),
    "e": (530.0, 1840.0, 2480.0, 0.02),
    "i": (270.0, 2290.0, 3010.0, 0.02),
    "o": (570.0, 840.0, 2410.0, 0.02),
    "u": (300.0, 870.0, 2240.0, 0.02),
    "y": (310.0, 2050.0, 2700.0, 0.03),
    "w": (320.0, 760.0, 2200.0, 0.03),
    "r": (490.0, 1350.0, 1690.0, 0.04),
    "l": (360.0, 1300.0, 2700.0, 0.04),
    "m": (280.0, 900.0, 2200.0, 0.03),
    "n": (300.0, 1450.0, 2450.0, 0.03),
    "s": (400.0, 1800.0, 3200.0, 0.35),
    "z": (340.0, 1750.0, 3000.0, 0.22),
    "f": (450.0, 1400.0, 2800.0, 0.28),
    "v": (350.0, 1350.0, 2650.0, 0.16),
    "t": (420.0, 1700.0, 2850.0, 0.25),
    "d": (360.0, 1650.0, 2700.0, 0.12),
    "k": (460.0, 1500.0, 2500.0, 0.22),
    "g": (380.0, 1480.0, 2450.0, 0.12),
    "p": (410.0, 1100.0, 2300.0, 0.20),
    "b": (340.0, 1080.0, 2250.0, 0.10),
    "h": (550.0, 1500.0, 2500.0, 0.30),
}


@register_model
class FormantTTSSynthesizer(BaseAIModel):
    """Coarticulated Formant Text-to-Speech synthesizer generating 16-bit PCM WAV audio with prosody."""

    metadata = ModelMetadata(
        key="voice",
        name="AI Voice Generator",
        category="Audio / TTS",
        task="Text-to-Speech Waveform Synthesis",
        description="Converts text into coarticulated F1/F2/F3 formant-modulated harmonic PCM WAV audio with prosody.",
        input_example={"text": "Hello tblinc AI", "pitch_hz": 165.0, "speed": 1.0},
        tags=["tts", "speech", "audio", "wav", "synthesis"],
    )

    def __init__(self, sample_rate: int = 8000, base_pitch_hz: float = 160.0) -> None:
        super().__init__()
        self.sample_rate = max(4000, sample_rate)
        self.base_pitch_hz = base_pitch_hz
        self.voice_profiles: dict[str, dict[str, float]] = {}

    def fit(self, voice_profiles: dict[str, dict[str, float]] | None = None) -> FormantTTSSynthesizer:
        defaults = {
            "neutral": {"pitch_hz": self.base_pitch_hz, "brightness": 0.60, "formant_scale": 1.00},
            "warm": {"pitch_hz": 130.0, "brightness": 0.45, "formant_scale": 0.94},
            "bright": {"pitch_hz": 210.0, "brightness": 0.80, "formant_scale": 1.08},
            "studio": {"pitch_hz": 175.0, "brightness": 0.70, "formant_scale": 1.02},
            "deep": {"pitch_hz": 115.0, "brightness": 0.40, "formant_scale": 0.90},
        }
        self.voice_profiles = dict(defaults)
        if voice_profiles:
            for k, v in voice_profiles.items():
                merged = dict(defaults["neutral"])
                merged.update({str(pk): float(pv) for pk, pv in v.items()})
                self.voice_profiles[str(k)] = merged
        self.is_fitted = True
        self.trained_at = time.time()
        self.training_metrics = {"sample_rate": self.sample_rate, "voices": sorted(self.voice_profiles)}
        return self

    def synthesize_wav(
        self,
        text: str,
        pitch_hz: float = 160.0,
        speed: float = 1.0,
        brightness: float = 0.6,
        formant_scale: float = 1.0,
    ) -> tuple[bytes, float, int]:
        clean = text.strip() or "hello"
        is_question = clean.endswith("?")
        char_dur = max(0.025, 0.065 / max(0.25, speed))
        samples_per_char = int(self.sample_rate * char_dur)
        pcm_samples: list[int] = []
        rng = random.Random(42)

        chars = list(clean.lower())
        total_chars = max(1, len(chars))
        prev_f1, prev_f2, prev_f3 = 500.0, 1500.0, 2500.0

        for idx, ch in enumerate(chars):
            if ch.isspace() or ch in ",.;:!?-":
                pause_len = samples_per_char if ch in ".!?" else (samples_per_char // 2)
                pcm_samples.extend([0] * pause_len)
                continue

            f1, f2, f3, noise_amp = _PHONEME_FORMANTS.get(
                ch,
                (440.0 + (ord(ch) % 10) * 30.0, 1250.0 + (ord(ch) % 7) * 85.0, 2450.0, 0.06),
            )
            f1 *= formant_scale
            f2 *= formant_scale
            f3 *= formant_scale

            # Prosody intonation curve across sentence
            pos = idx / total_chars
            prosody = (1.0 + 0.12 * pos) if is_question else (1.04 - 0.10 * pos)
            pitch = pitch_hz * prosody * (1.0 + 0.03 * math.sin(idx * 0.8))

            for n in range(samples_per_char):
                t = n / self.sample_rate
                blend = n / max(1, samples_per_char)
                # Smooth vocal-tract coarticulation transition from previous phoneme
                cur_f1 = prev_f1 + (f1 - prev_f1) * min(1.0, blend * 2.5)
                cur_f2 = prev_f2 + (f2 - prev_f2) * min(1.0, blend * 2.5)
                cur_f3 = prev_f3 + (f3 - prev_f3) * min(1.0, blend * 2.5)

                env = math.sin(math.pi * blend) ** 0.75
                glottal = 0.46 * math.sin(2.0 * math.pi * pitch * t) + 0.16 * math.sin(4.0 * math.pi * pitch * t)
                formants = (
                    0.24 * math.sin(2.0 * math.pi * cur_f1 * t)
                    + (0.14 * brightness) * math.sin(2.0 * math.pi * cur_f2 * t)
                    + (0.06 * brightness) * math.sin(2.0 * math.pi * cur_f3 * t)
                )
                fricative = noise_amp * (rng.uniform(-0.5, 0.5)) if noise_amp > 0.08 else 0.0
                val = env * (glottal + formants + fricative)
                pcm_samples.append(max(-32767, min(32767, int(val * 25000))))

            prev_f1, prev_f2, prev_f3 = f1, f2, f3

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(struct.pack(f"<{len(pcm_samples)}h", *pcm_samples))
        wav_bytes = buf.getvalue()
        duration_sec = len(pcm_samples) / self.sample_rate
        return wav_bytes, duration_sec, len(pcm_samples)

    @timed_predict
    def predict(self, data: str | dict[str, Any]) -> PredictionResult:
        if not self.is_fitted:
            raise RuntimeError("FormantTTSSynthesizer must be fitted before predict().")
        if isinstance(data, dict):
            text = str(data.get("text", "Hello tblinc"))
            voice = str(data.get("voice", "neutral"))
            prof = self.voice_profiles.get(voice, {"pitch_hz": self.base_pitch_hz, "brightness": 0.6, "formant_scale": 1.0})
            pitch_hz = float(data.get("pitch_hz", prof.get("pitch_hz", self.base_pitch_hz)))
            brightness = float(prof.get("brightness", 0.6))
            formant_scale = float(prof.get("formant_scale", 1.0))
            speed = float(data.get("speed", 1.0))
        else:
            text = str(data)
            voice = "neutral"
            pitch_hz = self.base_pitch_hz
            brightness = 0.6
            formant_scale = 1.0
            speed = 1.0

        wav_bytes, dur, n_samples = self.synthesize_wav(
            text,
            pitch_hz=pitch_hz,
            speed=speed,
            brightness=brightness,
            formant_scale=formant_scale,
        )
        raw_pcm = wav_bytes[44:]
        total_ints = len(raw_pcm) // 2
        bars: list[float] = []
        if total_ints > 0:
            step = max(1, total_ints // 36)
            for i in range(0, total_ints, step):
                sample = struct.unpack_from("<h", raw_pcm, i * 2)[0]
                bars.append(round(min(1.0, abs(sample) / 26000.0), 3))
        bars = bars[:36]
        b64_full = base64.b64encode(wav_bytes).decode("ascii")
        return PredictionResult(
            model=self.metadata.key,
            prediction=f"Synthesized {dur:.2f}s PCM WAV ({len(wav_bytes)} bytes)",
            confidence=1.0,
            details={
                "text": text,
                "voice": voice,
                "sample_rate": self.sample_rate,
                "duration_sec": round(dur, 3),
                "num_samples": n_samples,
                "wav_bytes_len": len(wav_bytes),
                "waveform_bars": bars,
                "audio_data_uri": "data:audio/wav;base64," + b64_full,
                "wav_base64_preview": base64.b64encode(wav_bytes[:96]).decode("ascii"),
            },
        )

    def get_state(self) -> dict[str, Any]:
        return {
            "sample_rate": self.sample_rate,
            "base_pitch_hz": self.base_pitch_hz,
            "voice_profiles": self.voice_profiles,
        }

    def set_state(self, state: dict[str, Any]) -> None:
        self.sample_rate = int(state["sample_rate"])
        self.base_pitch_hz = float(state["base_pitch_hz"])
        self.voice_profiles = dict(state["voice_profiles"])

    def _run_demo(self, custom_input: Any = None) -> dict[str, Any]:
        self.fit()
        res = self.predict(custom_input or self.metadata.input_example)
        return {"training": self.training_metrics, "result": res.to_dict()}
