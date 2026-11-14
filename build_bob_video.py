# Video stage for the IBM Bob client demo: renders every frame with Pillow (parallel), pipes raw frames
# into ffmpeg, muxes build audio and writes output/IBM_Bob_Client_Demo.mp4 plus captions .srt.
# Usage (env as in build_bob_audio.py):
#   python build_bob_video.py render            # full video
#   python build_bob_video.py still <sec> [png] # single preview frame
#   python build_bob_video.py sheet [png]       # contact sheet, one frame per scene
#
# Change log
# Sat 14 Nov 2026 18:30 CET - Initial version: 14 scenes following IBM_Bob_Client_Demo_script_v2.md.

import subprocess
import sys
from multiprocessing import Pool, cpu_count

import imageio_ffmpeg
from PIL import Image, ImageDraw

import bob_scenes_a as A
import bob_scenes_b as B
import build_video as BV
import demo_common as C
from bob_ui import disclaimer, gh_mark

W, H, FPS = C.W, C.H, C.FPS
SCENE_FUNCS = [A.s0, A.s1, A.s2, A.s3, A.s4, A.s5, A.s6, B.s7, B.s8, B.s9, B.s10, B.s11, B.s12, B.s13]
OUT_NAME = "IBM_Bob_Client_Demo"


# Render one frame as a PIL image - Sat 14 Nov 2026 18:30 CET
def render(fi):
    t = fi / FPS
    total = C.TL[-1]["end"] + 1.0
    i = max(k for k, sc in enumerate(C.TL) if sc["start"] <= t)
    sc = C.TL[i]
    ts, dur = t - sc["start"], sc["end"] - sc["start"]
    img = Image.new("RGB", (W, H), BV.BG)
    d = ImageDraw.Draw(img)
    SCENE_FUNCS[i](img, d, ts)
    d = ImageDraw.Draw(img)
    if 3 <= i <= 11:
        disclaimer(d)
    if 7 <= i <= 11:
        gh_mark(d)
    f = 1.0
    if i > 0 and i not in (1, 2, 13):          # continuous name-plate scenes cut without a dip to black
        f = min(f, BV.ease(ts / 0.35))
    if i < len(C.TL) - 1:
        if i not in (0, 1, 12):
            f = min(f, BV.ease((dur - ts) / 0.35))
    else:
        f = min(f, BV.ease((total - t) / 1.0))
    if f < 1:
        img = Image.blend(Image.new("RGB", (W, H), BV.BLACK), img, f)
        d = ImageDraw.Draw(img)
    BV.caption(img, d, t)
    return img


# Pool worker: frame index to raw bytes - Sat 14 Nov 2026 18:30 CET
def render_bytes(fi):
    return render(fi).tobytes()


# Initialise timeline and captions (also run in each worker) - Sat 14 Nov 2026 18:30 CET
def init():
    C.load_timeline()
    BV.CAPS[:] = C.captions()


# Format seconds for SRT - Sat 14 Nov 2026 18:30 CET
def srt_time(s):
    ms = int(round(s * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


# Full render + mux - Sat 14 Nov 2026 18:30 CET
def main_render():
    init()
    C.OUT.mkdir(exist_ok=True)
    with open(C.OUT / f"{OUT_NAME}.srt", "w", encoding="utf-8") as f:
        for k, (a, b, s) in enumerate(BV.CAPS, 1):
            f.write(f"{k}\n{srt_time(a)} --> {srt_time(b)}\n{s}\n\n")
    total = C.TL[-1]["end"] + 1.0
    n = int(total * FPS)
    out = C.OUT / f"{OUT_NAME}.mp4"
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
    proc.wait()
    C.log.info("wrote %s", out)


# Preview a single frame - Sat 14 Nov 2026 18:30 CET
def main_still(sec, path):
    init()
    render(int(sec * FPS)).save(path)


# Contact sheet: three frames per scene (25%, 60%, 92%) as separate PNGs for review - Sat 14 Nov 2026 18:30 CET
def main_sheet(prefix):
    init()
    for i, sc in enumerate(C.TL):
        for tag, frac in (("a", 0.25), ("b", 0.6), ("c", 0.92)):
            t = sc["start"] + (sc["end"] - sc["start"]) * frac
            render(int(t * FPS)).resize((960, 540)).save(f"{prefix}_{i:02d}{tag}.png")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "still":
        main_still(float(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else str(C.BUILD / "still.png"))
    elif len(sys.argv) > 1 and sys.argv[1] == "sheet":
        main_sheet(sys.argv[2] if len(sys.argv) > 2 else str(C.BUILD / "sheet"))
    else:
        main_render()
