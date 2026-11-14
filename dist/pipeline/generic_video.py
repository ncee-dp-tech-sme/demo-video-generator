# Generic video stage for step 9 (video production): renders every scene of an approved script as an animated mock
# screen (terminal, browser, IDE with assistant panel, architecture flow, cards, checklist, stats, feed, split screens)
# with burned-in captions, pipes the frames to the ffmpeg bundled in imageio-ffmpeg and muxes the audio from
# generic_audio.py. Also writes the .srt file.
# What is drawn per scene comes from the storyboard (storyboard.py): an automatic plan made from the script text,
# overridden scene by scene by narratives/<slug>/storyboard.json when that file exists (STORYBOARD_FILE).
# The drawing itself is in scene_engine.py. The screens are illustrations, not product footage.
# Started by tools/production.py with SCRIPT_FILE, BUILD_DIR, VIDEO_OUT_DIR and VIDEO_NAME set.
#
# Usage: python generic_video.py render | still <sec> <png> | sheet <prefix>
#
# Change log
# Sat 14 Nov 2026 19:28 CET - Initial version (storyboard text cards).
# Sat 14 Nov 2026 22:00 CET - Animated scenes from storyboard + scene_engine; estimated timeline when audio is not built yet.

import os
import re
import subprocess
import sys
from multiprocessing import Pool, cpu_count
from pathlib import Path

sys.path.insert(0, os.environ["DEMOBUILDER_DIR"])

import imageio_ffmpeg  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

import build_video as BV  # noqa: E402
import demo_common as C  # noqa: E402
import scene_engine as SE  # noqa: E402
import storyboard as SB  # noqa: E402

W, H, FPS = C.W, C.H, C.FPS
OUT_DIR = Path(os.environ["VIDEO_OUT_DIR"]).resolve()
NAME = re.sub(r"[^A-Za-z0-9_-]", "", os.environ.get("VIDEO_NAME", "")) or "narrative"
STORYBOARD = {}   # filled by init()


# Output file path inside OUT_DIR only - Sat 14 Nov 2026 19:28 CET
def out_path(suffix):
    p = (OUT_DIR / f"{NAME}{suffix}").resolve()
    if not p.is_relative_to(OUT_DIR):
        raise SystemExit("output path escapes the output folder")
    return p


# Timeline estimated from the script text (no audio yet): speech speed from SPEECH_RATE words per minute - Sat 14 Nov 2026 22:00 CET
def estimate_timeline():
    tl = []
    for sc in C.SCENES:
        start = tl[-1]["end"] if tl else sc["start"]
        cursor, parts = C.LEAD_IN, C.split_parts(sc["vo"])
        out = []
        for k, p in enumerate(parts):
            dur = max(0.8, len(p.split()) * 60.0 / C.SPEECH_RATE)
            out.append({"text": p, "t0": cursor, "dur": dur})
            cursor += dur + (C.BEAT_GAP if k < len(parts) - 1 else 0)
        end = max(sc["end"], start + cursor + C.TAIL)
        tl.append({"start": start, "end": end, "rate": C.SPEECH_RATE, "parts": out})
    return tl


# Load the real timeline written by the audio stage, or an estimate when it does not exist yet - Sat 14 Nov 2026 22:00 CET
def load_timeline():
    if C.TIMELINE_JSON.is_file():
        return C.load_timeline()
    C.load_scenes()
    return C.set_timeline(estimate_timeline())


# Load storyboard (user file merged over the automatic plan); returns the problems found - Sat 14 Nov 2026 22:00 CET
def load_storyboard():
    sb, problems = SB.load(C.SCRIPT_MD, os.environ.get("STORYBOARD_FILE") or None)
    STORYBOARD.clear()
    STORYBOARD.update(sb)
    return problems


# Render one frame as a PIL image - Sat 14 Nov 2026 19:28 CET
def render(fi):
    t = fi / FPS
    total = C.TL[-1]["end"] + 1.0
    i = max(k for k, sc in enumerate(C.TL) if sc["start"] <= t)
    sc = C.TL[i]
    ts, dur = t - sc["start"], sc["end"] - sc["start"]
    img = Image.new("RGB", (W, H), BV.BG)
    img = SE.draw_scene(img, i, ts, dur, STORYBOARD["scenes"][i], STORYBOARD.get("style"))
    f = min(BV.ease(ts / 0.3) if i > 0 else 1.0,
            BV.ease((dur - ts) / 0.3) if i < len(C.TL) - 1 else BV.ease((total - t) / 1.0))
    if f < 1:
        img = Image.blend(Image.new("RGB", (W, H), BV.BLACK), img, f)
    BV.caption(img, ImageDraw.Draw(img), t)
    return img


# Pool worker: frame index to raw bytes - Sat 14 Nov 2026 19:28 CET
def render_bytes(fi):
    return render(fi).tobytes()


# Initialise timeline, storyboard and captions (also run in each worker) - Sat 14 Nov 2026 22:00 CET
def init(announce=False):
    load_timeline()
    problems = load_storyboard()
    if announce:
        for p in problems:
            C.log.warning("storyboard: %s", p)
        if len(STORYBOARD["scenes"]) != len(C.TL):
            raise SystemExit("storyboard and script have different scene counts")
    BV.CAPS[:] = C.captions()


# Format seconds for SRT - Sat 14 Nov 2026 19:28 CET
def srt_time(s):
    ms = int(round(s * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


# Full render and mux - Sat 14 Nov 2026 19:28 CET
def main_render():
    if not C.TIMELINE_JSON.is_file() or not (C.BUILD / "audio.wav").is_file():
        raise SystemExit("audio not built yet: run the audio stage first")
    init(announce=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with out_path(".srt").open("w", encoding="utf-8") as f:
        for k, (a, b, s) in enumerate(BV.CAPS, 1):
            f.write(f"{k}\n{srt_time(a)} --> {srt_time(b)}\n{s}\n\n")
    n = int((C.TL[-1]["end"] + 1.0) * FPS)
    out = out_path(".mp4")
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(C.BUILD / "audio.wav"),
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(max(1, cpu_count() - 1), initializer=init) as pool:
        for k, frame in enumerate(pool.imap(render_bytes, range(n), chunksize=6)):
            proc.stdin.write(frame)
            if k % 240 == 0:
                C.log.info("frame %d/%d", k, n)
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit("ffmpeg failed")
    C.log.info("wrote %s", out)


# One review frame per scene at 60 percent of its window - Sat 14 Nov 2026 19:28 CET
def main_sheet(prefix):
    init(announce=True)
    for i, sc in enumerate(C.TL):
        t = sc["start"] + (sc["end"] - sc["start"]) * 0.6
        render(int(t * FPS)).resize((960, 540)).save(f"{prefix}_{i:02d}.png")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "render"
    if cmd == "still":
        init(announce=True)
        render(int(float(sys.argv[2]) * FPS)).save(sys.argv[3])
    elif cmd == "sheet":
        main_sheet(sys.argv[2])
    else:
        main_render()
