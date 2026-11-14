# Generic video stage for step 9 (video production): renders every scene of an approved script as a storyboard
# card (scene title, ON-SCREEN text, SCENE description, DEMO text) with burned-in captions, pipes the frames to
# the ffmpeg bundled in imageio-ffmpeg and muxes the audio from generic_audio.py. Also writes the .srt file.
# The cards are placeholders: story-specific renderers (like the IBM Bob scenes) give higher visual fidelity.
# Started by tools/production.py with SCRIPT_FILE, BUILD_DIR, VIDEO_OUT_DIR and VIDEO_NAME set.
#
# Usage: python generic_video.py render | still <sec> <png> | sheet <prefix>
#
# Change log
# Sat 14 Nov 2026 19:28 CET - Initial version.

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

W, H, FPS = C.W, C.H, C.FPS
OUT_DIR = Path(os.environ["VIDEO_OUT_DIR"]).resolve()
NAME = re.sub(r"[^A-Za-z0-9_-]", "", os.environ.get("VIDEO_NAME", "")) or "narrative"


# Output file path inside OUT_DIR only - Sat 14 Nov 2026 19:28 CET
def out_path(suffix):
    p = (OUT_DIR / f"{NAME}{suffix}").resolve()
    if not p.is_relative_to(OUT_DIR):
        raise SystemExit("output path escapes the output folder")
    return p


# Split a VISUAL cell into its labelled parts, markdown removed - Sat 14 Nov 2026 19:28 CET
def visual_parts(cell):
    out = {}
    for chunk in re.split(r"<br\s*/?>", cell):
        m = re.match(r"\s*\**\s*(SCENE|ON-SCREEN|DEMO|TRANSITION)\s*:\s*\**\s*(.*)", chunk, re.I | re.S)
        if m:
            out[m.group(1).upper()] = re.sub(r"[*`_]", "", m.group(2)).strip()
    if not out:
        out["SCENE"] = re.sub(r"[*`_]|<br\s*/?>", " ", cell).strip()
    return out


# Wrap text to a pixel width - Sat 14 Nov 2026 19:28 CET
def wrap(text, f, width, limit=6):
    lines, cur = [], ""
    for w in text.split():
        trial = (cur + " " + w).strip()
        if f.getlength(trial) > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    lines.append(cur)
    return lines[:limit]


# Draw one storyboard card for scene i - Sat 14 Nov 2026 19:28 CET
def card(d, i, n, parts):
    BV.T(d, (120, 90), f"SCENE {i + 1} OF {n}", BV.font(30, True), BV.CYAN)
    d.line((120, 140, 380, 140), fill=BV.CYAN, width=4)
    headline = parts.get("ON-SCREEN") or parts.get("SCENE", "")
    f = BV.font(64, True)
    y = 260
    for ln in wrap(headline, f, 1600, 4):
        BV.T(d, (120, y), ln, f, BV.TXT)
        y += 84
    if "ON-SCREEN" in parts and "SCENE" in parts:
        y += 30
        for ln in wrap(parts["SCENE"], BV.font(34), 1600, 3):
            BV.T(d, (120, y), ln, BV.font(34), BV.MUTED)
            y += 48
    if "DEMO" in parts:
        BV.box(d, (120, 700, 1800, 900), fill=BV.PANEL, outline=BV.LINE)
        BV.T(d, (150, 720), "DEMO", BV.font(26, True), BV.AMBER)
        yy = 770
        for ln in wrap(parts["DEMO"], BV.font(30, mono=True), 1600, 3):
            BV.T(d, (150, yy), ln, BV.font(30, mono=True), BV.TXT)
            yy += 40
    BV.T(d, (W - 120, 930), "Storyboard render: placeholder visuals", BV.font(24), BV.MUTED, "ra")


# Render one frame as a PIL image - Sat 14 Nov 2026 19:28 CET
def render(fi):
    t = fi / FPS
    total = C.TL[-1]["end"] + 1.0
    i = max(k for k, sc in enumerate(C.TL) if sc["start"] <= t)
    sc = C.TL[i]
    ts, dur = t - sc["start"], sc["end"] - sc["start"]
    img = Image.new("RGB", (W, H), BV.BG)
    card(ImageDraw.Draw(img), i, len(C.TL), visual_parts(C.SCENES[i]["visual"]))
    f = min(BV.ease(ts / 0.3) if i > 0 else 1.0,
            BV.ease((dur - ts) / 0.3) if i < len(C.TL) - 1 else BV.ease((total - t) / 1.0))
    if f < 1:
        img = Image.blend(Image.new("RGB", (W, H), BV.BLACK), img, f)
    BV.caption(img, ImageDraw.Draw(img), t)
    return img


# Pool worker: frame index to raw bytes - Sat 14 Nov 2026 19:28 CET
def render_bytes(fi):
    return render(fi).tobytes()


# Initialise timeline and captions (also run in each worker) - Sat 14 Nov 2026 19:28 CET
def init():
    C.load_timeline()
    BV.CAPS[:] = C.captions()


# Format seconds for SRT - Sat 14 Nov 2026 19:28 CET
def srt_time(s):
    ms = int(round(s * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


# Full render and mux - Sat 14 Nov 2026 19:28 CET
def main_render():
    init()
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
    init()
    for i, sc in enumerate(C.TL):
        t = sc["start"] + (sc["end"] - sc["start"]) * 0.6
        render(int(t * FPS)).resize((960, 540)).save(f"{prefix}_{i:02d}.png")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "render"
    if cmd == "still":
        init()
        render(int(float(sys.argv[2]) * FPS)).save(sys.argv[3])
    elif cmd == "sheet":
        main_sheet(sys.argv[2])
    else:
        main_render()
