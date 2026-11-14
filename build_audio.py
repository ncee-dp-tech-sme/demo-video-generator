# Audio stage: synthesises the voice-over with macOS `say`, fits it to each scene window,
# builds timeline.json, and mixes VO + ambient bed + sfx into build/audio.wav.
#
# Change log
# Sat 14 Nov 2026 17:30 CET - Initial version.
# Sat 14 Nov 2026 17:40 CET - Cap speech rate at 235 wpm; borrow time from next scene instead.

import json
import subprocess
import wave

import numpy as np

import demo_common as C

SR = 44100
LOCK_CUE = (5, "Guardrails on")   # scene index + phrase; shared with the video stage


# Synthesise one text part to a wav file and return samples - Sat 14 Nov 2026 17:30 CET
def synth(text, rate, path):
    subprocess.run(
        ["say", "-v", C.VOICE, "-r", str(rate), "-o", str(path),
         f"--data-format=LEI16@{SR}", C.tts_text(text)],
        check=True, timeout=120)
    with wave.open(str(path), "rb") as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


# Fit a scene's VO inside its window by raising the speech rate if needed - Sat 14 Nov 2026 17:30 CET
def build_scene(i, sc):
    window = sc["end"] - sc["start"]
    rate_cap = 235   # keep the voice intelligible; extend the scene instead of rushing further
    parts = C.split_parts(sc["vo"])
    rate = C.SPEECH_RATE
    while True:
        wavs = [synth(p, rate, C.BUILD / f"vo_{i}_{k}.wav") for k, p in enumerate(parts)]
        cursor, out = C.LEAD_IN, []
        for k, (p, w) in enumerate(zip(parts, wavs)):
            dur = len(w) / SR
            out.append({"text": p, "t0": cursor, "dur": dur})
            cursor += dur + (C.BEAT_GAP if k < len(parts) - 1 else 0)
        if cursor <= window - C.TAIL or rate + 8 > rate_cap:
            break
        rate += 8
    end = sc["end"]
    if cursor > window - C.TAIL:   # still too long: borrow time from the next scene
        extra = cursor + C.TAIL - window
        end += extra
        C.log.warning("scene %d extended by %.1fs (rate %d)", i, extra, rate)
    C.log.info("scene %d: rate=%d vo_end=%.1fs window=%.1fs", i, rate, cursor, end - sc["start"])
    return {"start": sc["start"], "end": end, "rate": rate, "parts": out}, wavs


# Mix a sample array into the track at a given time - Sat 14 Nov 2026 17:30 CET
def put(track, samples, t, gain=1.0):
    a = int(t * SR)
    b = min(len(track), a + len(samples))
    if a < len(track):
        track[a:b] += samples[: b - a] * gain


# Short sine blip with fade - Sat 14 Nov 2026 17:30 CET
def blip(freq, dur, vol=0.3):
    t = np.arange(int(dur * SR)) / SR
    return (np.sin(2 * np.pi * freq * t) * np.exp(-t * 6 / dur) * vol).astype(np.float32)


# Harsh two-tone buzzer for the blocked banner - Sat 14 Nov 2026 17:30 CET
def buzzer(dur=0.7, vol=0.25):
    t = np.arange(int(dur * SR)) / SR
    sq = np.sign(np.sin(2 * np.pi * 110 * t)) + np.sign(np.sin(2 * np.pi * 123 * t))
    env = np.minimum(1, t * 50) * np.minimum(1, (dur - t) * 20)
    return (sq * 0.5 * env * vol).astype(np.float32)


# Mechanical click for the lock snapping shut - Sat 14 Nov 2026 17:30 CET
def click(vol=0.5):
    rng = np.random.default_rng(3)
    t = np.arange(int(0.12 * SR)) / SR
    return (rng.standard_normal(len(t)) * np.exp(-t * 60) * vol
            + np.sin(2 * np.pi * 180 * t) * np.exp(-t * 40) * 0.4).astype(np.float32)


# Soft rising pad swell for the title card - Sat 14 Nov 2026 17:30 CET
def swell(dur=4.0, vol=0.12):
    t = np.arange(int(dur * SR)) / SR
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    s = sum(np.sin(2 * np.pi * f * t) for f in (110, 164.8, 220, 329.6)) / 4
    return (s * env * vol).astype(np.float32)


# Low ambient drone under the whole video - Sat 14 Nov 2026 17:30 CET
def ambient(n, vol=0.035):
    t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * t + k) * (0.6 + 0.4 * np.sin(2 * np.pi * lf * t))
            for k, (f, lf) in enumerate([(55, 0.07), (82.4, 0.05), (110, 0.09), (164.8, 0.04)])) / 4
    fade = np.minimum(1, np.minimum(t / 2, (n / SR - t) / 3))
    return (s * fade * vol).astype(np.float32)


# Run the whole audio stage - Sat 14 Nov 2026 17:30 CET
def main():
    C.BUILD.mkdir(exist_ok=True)
    scenes = C.load_scenes()
    tl, vo_wavs = [], []
    for i, sc in enumerate(scenes):
        if tl:
            sc["start"] = tl[-1]["end"]   # follow any extension of the previous scene
        entry, wavs = build_scene(i, sc)
        tl.append(entry)
        vo_wavs.append(wavs)
    C.TIMELINE_JSON.write_text(json.dumps(tl, indent=1))
    C.set_timeline(tl)

    total = scenes[-1]["end"] + 1.0
    track = np.zeros(int(total * SR), dtype=np.float32)
    for entry, wavs in zip(tl, vo_wavs):
        for part, w in zip(entry["parts"], wavs):
            put(track, w, entry["start"] + part["t0"], 1.0)
    voice_peak = float(np.max(np.abs(track))) or 1.0
    track *= 0.9 / voice_peak
    track += ambient(len(track))

    for k in range(6):                                   # boot-line ticks
        put(track, blip(1200, 0.05, 0.15), 0.3 + k * 0.45)
    put(track, buzzer(), tl[4]["start"] + 0.05)           # SCAN BLOCKED
    put(track, click(), tl[LOCK_CUE[0]]["start"] + C.cue(*LOCK_CUE))
    put(track, swell(), tl[8]["start"] + C.cue(8, "HexStrike just hired") - 0.5)

    pcm = (np.clip(track, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(C.BUILD / "audio.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    C.log.info("audio written: %.1fs", total)


if __name__ == "__main__":
    main()
