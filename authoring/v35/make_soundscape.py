"""Generate original mall ambience and shoe Foley. All sounds are synthesized."""
from pathlib import Path
import subprocess
import wave

import numpy as np

OUT = Path(__file__).resolve().parents[2] / "assets" / "v35" / "sound"
OUT.mkdir(parents=True, exist_ok=True)
RATE = 24000
rng = np.random.default_rng(35036)


def colored(length, lo, hi, shape=2):
    """Circular filtered noise, safe to loop without a sample discontinuity."""
    f = np.fft.rfftfreq(length, 1 / RATE)
    with np.errstate(over="ignore", divide="ignore"):
        low = 1 / np.sqrt(1 + np.power(lo / np.maximum(f, 1e-6), 2 * shape))
        high = 1 / np.sqrt(1 + np.power(f / hi, 2 * shape))
    data = np.fft.irfft(np.fft.rfft(rng.normal(size=length)) * low * high, n=length)
    return data / max(data.std(), 1e-8)


def save_wav(path, samples):
    with wave.open(str(path), "wb") as wavefile:
        wavefile.setnchannels(samples.shape[1] if samples.ndim == 2 else 1)
        wavefile.setsampwidth(2)
        wavefile.setframerate(RATE)
        wavefile.writeframes(np.int16(np.clip(samples, -.98, .98) * 32767).tobytes())


def ambience(name, air_gain, fan_gain, hall_gain, wind_gain):
    duration = 16
    n = duration * RATE
    t = np.arange(n) / RATE
    air = colored(n, 113, 850) * air_gain
    hall = colored(n, 189, 1600)
    drift = .84 + .12 * np.cos(2 * np.pi * 3 * t / duration) + .04 * np.sin(2 * np.pi * 7 * t / duration)
    wind = colored(n, 41, 235) * wind_gain * drift**3
    fan = (np.sin(2 * np.pi * 65 * t) + .23 * np.sin(2 * np.pi * 130 * t)) * fan_gain
    core = air + hall * hall_gain * drift + wind + fan
    channels = [core + colored(n, 210, 2100) * .015 for _ in range(2)]
    source = OUT / (name + ".wav")
    save_wav(source, np.stack(channels, axis=1))
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
                    "-c:a", "libvorbis", "-q:a", "4", str(OUT / (name + ".ogg"))], check=True)
    source.unlink()


def step(name, index, indoor):
    n = int(RATE * .26)
    t = np.arange(n) / RATE
    heel = (1 - np.exp(-t * 730)) * np.exp(-t * rng.uniform(36, 54))
    body = colored(n, 72, 380) * .29 * heel
    scuff_origin = rng.uniform(.054, .072)
    u = np.maximum(t - scuff_origin, 0)
    scuff = np.exp(-u * 49) * (1 - np.exp(-u * 540))
    grit = colored(n, 420, 1900 if indoor else 3400) * (.064 if indoor else .087) * scuff
    click = (np.sin(2 * np.pi * rng.uniform(160, 220) * t) * .10 +
             colored(n, 750, 3250) * (.13 if indoor else .073)) * heel
    shoe = body + grit + click
    if indoor:
        for seconds, gain in ((.013, .17), (.031, .08), (.045, .035)):
            shift = int(seconds * RATE)
            shoe[shift:] += shoe[:-shift] * gain
    step_fade = np.minimum(1, (n - np.arange(n)) / 400)
    save_wav(OUT / f"{name}_{index}.wav", .62 * shoe * step_fade)


ambience("interior", .037, .014, .014, .004)
ambience("court", .018, 0.0, .007, .057)
for i in range(5):
    step("tile", i, True)
    step("paving", i, False)
