# Audio stage for the IBM Bob client demo: synthesises the VO with macOS `say`, fits it to each
# scene window (reusing build_audio helpers), writes timeline.json and mixes VO + ambient bed + sfx.
# Run with: SCRIPT_FILE=IBM_Bob_Client_Demo_script_v2.md BUILD_DIR=build/bob SPEECH_RATE=150 python build_bob_audio.py
#
# Change log
# Sat 14 Nov 2026 18:00 CET - Initial version for IBM_Bob_Client_Demo_script_v2.md.

import json
import wave

import numpy as np

import demo_common as C
from build_audio import SR, ambient, blip, build_scene, click, put, swell

TITLE_SCENES = (3, 7)                                   # Part 1 / Part 2 title cards
PASS_CUES = [(6, "Sixteen passing"), (10, "All green")]  # test-pass clicks
TICK_CUES = [(0, "Every engineering"), (1, "Boilerplate"), (1, "Context switching"), (1, "And governance"),
             (12, "One:"), (12, "Two:"), (12, "Three:"), (12, "Four:"), (12, "And five"),
             (13, "A hands-on workshop"), (13, "A deeper product dive"), (13, "Or a Proof of Experience")]


# Run the whole audio stage - Sat 14 Nov 2026 18:00 CET
def main():
    C.BUILD.mkdir(parents=True, exist_ok=True)
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

    total = tl[-1]["end"] + 1.0
    track = np.zeros(int(total * SR), dtype=np.float32)
    for entry, wavs in zip(tl, vo_wavs):
        for part, w in zip(entry["parts"], wavs):
            put(track, w, entry["start"] + part["t0"], 1.0)
    voice_peak = float(np.max(np.abs(track))) or 1.0
    track *= 0.9 / voice_peak
    track += ambient(len(track), vol=0.03)

    for i in TITLE_SCENES:
        put(track, swell(3.0, 0.12), tl[i]["start"] + 0.2)
    for i, phrase in PASS_CUES:
        put(track, click(0.35), tl[i]["start"] + C.cue(i, phrase))
    for i, phrase in TICK_CUES:
        put(track, blip(1400, 0.06, 0.08), tl[i]["start"] + C.cue(i, phrase) + 0.05)

    pcm = (np.clip(track, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(C.BUILD / "audio.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    C.log.info("audio written: %.1fs", total)


if __name__ == "__main__":
    main()
