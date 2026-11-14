# Generic audio stage for step 9 (video production): voice-over with macOS `say`, fitted to each scene window,
# timeline.json and a mixed audio.wav (voice + quiet ambient bed). Works for any approved script table.
# Reuses the Demobuilder primitives (demo_common, build_audio) found in DEMOBUILDER_DIR.
# Started by tools/production.py with SCRIPT_FILE, BUILD_DIR, SPEECH_RATE and VOICE set; not meant to be run by hand.
#
# Change log
# Sat 14 Nov 2026 19:28 CET - Initial version.

import json
import os
import sys
import wave

sys.path.insert(0, os.environ["DEMOBUILDER_DIR"])

import numpy as np  # noqa: E402

import demo_common as C  # noqa: E402
from build_audio import SR, ambient, build_scene, put  # noqa: E402


# Run the audio stage - Sat 14 Nov 2026 19:28 CET
def main():
    C.BUILD.mkdir(parents=True, exist_ok=True)
    scenes = C.load_scenes()
    tl, vo_wavs = [], []
    for i, sc in enumerate(scenes):
        if tl:
            sc["start"] = tl[-1]["end"]          # follow any extension of the previous scene
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
    track *= 0.9 / (float(np.max(np.abs(track))) or 1.0)
    track += ambient(len(track), vol=0.03)

    pcm = (np.clip(track, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(C.BUILD / "audio.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    C.log.info("audio written: %.1fs", total)


if __name__ == "__main__":
    main()
