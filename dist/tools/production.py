# Step 9 (video production): gate check, prerequisite check and staged run of the audio/video pipeline for an
# approved script. Refuses to run unless approval.py verifies the exact script file and the script validates.
#
# Usage:
#   python production.py check <script.md>
#   python production.py storyboard <script.md> [--force]      (writes the draft storyboard.json next to the script)
#   python production.py run <script.md> --stage audio|still|sheet|video|all --confirmed [--at SEC]
#        [--custom-audio build_x_audio.py --custom-video build_x_video.py]
# Output (inside the script's folder): storyboard.json, production/build, production/review, production/output, production.json
# Exit codes: 0 ok, 1 gate or prerequisite failed or a stage failed, 2 unusable input.
#
# Change log
# Sat 14 Nov 2026 19:28 CET - Initial version: gate check, prerequisites, audio/still/sheet/video stages.
# Sat 14 Nov 2026 21:09 CET - Pipeline files are bundled in pipeline/, which is the default when DEMOBUILDER_DIR is unset;
#                             default Python falls back to the installer's .venv.
# Sat 14 Nov 2026 22:03 CET - Storyboard: `storyboard` command writes storyboard.json; check reports it; stages get STORYBOARD_FILE.

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import approval
import common as C
import validate_script as V

PIPELINE_DIR = C.PIPELINE_DIR
sys.path.insert(0, str(PIPELINE_DIR))
import storyboard as SB  # noqa: E402  (pure Python, no Pillow needed)

CUSTOM_NAME = re.compile(r"^build_[A-Za-z0-9_]+\.py$")
FONT = Path("/System/Library/Fonts/HelveticaNeue.ttc")
STAGE_TIMEOUT = {"audio": 1800, "still": 300, "sheet": 900, "video": 7200}
ROW = re.compile(r"^\|\s*(\d+):(\d+)\s*[–-]\s*(\d+):(\d+)", re.M)


# Folder of the Demobuilder pipeline from .env; defaults to the bundled pipeline/ folder - Sat 14 Nov 2026 21:09 CET
def demobuilder_dir():
    return Path(C.DEMOBUILDER_DIR).expanduser().resolve()


# Interpreter that has pillow, numpy and imageio-ffmpeg - Sat 14 Nov 2026 21:09 CET
def pipeline_python():
    if C.PIPELINE_PYTHON:
        return C.PIPELINE_PYTHON
    for base in (demobuilder_dir(), C.HOME):          # pipeline folder venv, then the installer's venv
        cand = base / ".venv" / "bin" / "python"
        if cand.is_file():
            return str(cand)
    return sys.executable


# Storyboard that step 9 will use for a script: source, layout per scene and problems found - Sat 14 Nov 2026 22:03 CET
def storyboard_info(script):
    try:
        sb, problems = SB.load(script)
    except (OSError, ValueError) as exc:
        return {"source": "none", "layouts": [], "problems": [f"storyboard could not be built: {type(exc).__name__}"]}
    return {"source": sb["source"], "layouts": [s["layout"] for s in sb["scenes"]], "problems": problems}


# Write the draft storyboard.json next to the script; never overwrites without force - Sat 14 Nov 2026 22:03 CET
def write_storyboard(script, force=False):
    script = Path(script).expanduser().resolve()
    out = script.parent / "storyboard.json"
    if out.exists() and not force:
        return {"ok": False, "reason": f"{out.name} exists; pass --force to replace it", "path": str(out)}
    sb = SB.auto_storyboard(script.read_text(encoding="utf-8"))
    out.write_text(json.dumps(sb, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"ok": True, "path": str(out), "scenes": len(sb["scenes"]), "layouts": [s["layout"] for s in sb["scenes"]]}


# Check the approval gate, the script and the machine; returns a report dict - Sat 14 Nov 2026 19:28 CET
def check(script):
    script = Path(script).expanduser().resolve()
    problems = []
    appr = approval.verify(script)
    if not appr["ok"]:
        problems.append("approval: " + appr["reason"])
    val = V.validate(script.read_text(encoding="utf-8"), C.SPEECH_WPM, None, require_plan=True)
    problems += ["script: " + e for e in val["errors"]]

    demo = demobuilder_dir()
    if not demo.is_dir():
        problems.append(f"DEMOBUILDER_DIR is not a folder: {demo} (clear it in .env to use the bundled pipeline/)")
    else:
        problems += [f"pipeline file missing: {demo / n}" for n in ("demo_common.py", "build_audio.py", "build_video.py")
                     if not (demo / n).is_file()]
    problems += [f"pipeline file missing: {PIPELINE_DIR / n}" for n in
                 ("generic_audio.py", "generic_video.py", "scene_engine.py", "storyboard.py", "bob_ui.py")
                 if not (PIPELINE_DIR / n).is_file()]
    if sys.platform != "darwin" or not shutil.which("say"):
        problems.append("macOS `say` command not found (voice-over synthesis needs macOS)")
    if not FONT.is_file():
        problems.append(f"font not found: {FONT}")
    py = pipeline_python()
    try:
        r = subprocess.run([py, "-c", "import PIL, numpy, imageio_ffmpeg, dotenv"], capture_output=True, timeout=60)
        if r.returncode != 0:
            problems.append(f"{py} lacks pillow, numpy, imageio-ffmpeg or python-dotenv")
    except (OSError, subprocess.SubprocessError):
        problems.append(f"cannot run pipeline python {py}")
    sbi = storyboard_info(script)
    return {"ok": not problems, "script": script.name, "approval": appr, "pipeline_python": py,
            "demobuilder_dir": str(demo), "storyboard": sbi, "problems": problems,
            "warnings": val["warnings"] + ["storyboard: " + p for p in sbi["problems"]]}


# sha256 and size of an output file - Sat 14 Nov 2026 19:28 CET
def describe(path):
    p = Path(path)
    return {"path": str(p), "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}


# Run one pipeline stage as a subprocess without a shell - Sat 14 Nov 2026 19:28 CET
def run_stage(stage, args, script, dirs, py):
    demo = demobuilder_dir()
    env = {**os.environ, "DEMOBUILDER_DIR": str(demo), "SCRIPT_FILE": str(script),
           "BUILD_DIR": str(dirs["build"]), "VIDEO_OUT_DIR": str(dirs["output"]),
           "VIDEO_NAME": re.sub(r"_script_v\d+$", "", script.stem), "SPEECH_RATE": str(C.SPEECH_WPM),
           "VOICE": C.VOICE, "FPS": str(C.FPS), "STORYBOARD_FILE": str(script.parent / "storyboard.json")}
    if args.custom_audio:
        audio, video = str(demo / args.custom_audio), str(demo / args.custom_video)
    else:
        audio, video = str(PIPELINE_DIR / "generic_audio.py"), str(PIPELINE_DIR / "generic_video.py")
    if stage == "audio":
        cmd = [py, audio]
    elif stage == "video":
        cmd = [py, video, "render"]
    elif stage == "still":
        cmd = [py, video, "still", str(args.at), str(dirs["review"] / "still.png")]
    else:
        cmd = [py, video, "sheet", str(dirs["review"] / "sheet")]
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    started = time.time()
    r = subprocess.run(cmd, cwd=demo, env=env, capture_output=True, text=True, timeout=STAGE_TIMEOUT[stage])
    C.event(20 if r.returncode == 0 else 40, "production_stage", stage=stage, returncode=r.returncode)
    tail = (r.stderr or "").strip().splitlines()[-5:]
    return {"stage": stage, "returncode": r.returncode, "seconds": round(time.time() - started, 1),
            "log_tail": tail if C.DEBUG else ([] if r.returncode == 0 else ["stage failed; set LOG_LEVEL=DEBUG for details"])}


# Timeline facts after the audio stage: runtime and scenes that had to be extended - Sat 14 Nov 2026 19:28 CET
def timeline_facts(build_dir, script_text):
    f = build_dir / "timeline.json"
    if not f.is_file():
        return {}
    tl = json.loads(f.read_text(encoding="utf-8"))
    planned = [int(m.group(3)) * 60 + int(m.group(4)) for m in ROW.finditer(script_text)]
    extended = [i for i, (sc, end) in enumerate(zip(tl, planned)) if sc["end"] - end > 0.5]
    return {"runtime_seconds": round(tl[-1]["end"] + 1.0, 1), "scenes": len(tl), "scenes_extended": extended}


# Run the requested stage(s) and write production.json - Sat 14 Nov 2026 19:28 CET
def run(script, args):
    report = check(script)
    if not report["ok"]:
        return {"ok": False, "last_stage_ok": False, "reason": "gate or prerequisites failed",
                "problems": report["problems"]}
    script = Path(script).expanduser().resolve()
    folder = script.parent / "production"
    dirs = {"build": folder / "build", "review": folder / "review", "output": folder / "output"}
    stages = ["audio", "video"] if args.stage == "all" else [args.stage]
    pf = script.parent / "production.json"
    sha = approval.sha256(script)
    prev = {}
    if pf.is_file():
        try:
            prev = json.loads(pf.read_text(encoding="utf-8"))
        except ValueError:
            prev = {}
    if prev.get("script_sha256") != sha:
        prev = {}
    results, started, ran_ok = prev.get("stages", []), time.time(), True
    for st in stages:
        res = run_stage(st, args, script, dirs, report["pipeline_python"])
        results.append({**res, "at": datetime.now().astimezone().isoformat(timespec="seconds")})
        ran_ok = res["returncode"] == 0
        if not ran_ok:
            break
    outputs = [describe(p) for p in sorted(dirs["output"].glob("*")) if p.is_file()]
    if args.custom_video and not outputs:       # story-specific renderers write to <DEMOBUILDER_DIR>/output
        out = demobuilder_dir() / "output"
        outputs = [describe(p) for p in sorted(out.glob("*")) if p.is_file() and p.stat().st_mtime >= started]
    outputs += [describe(p) for p in sorted(dirs["review"].glob("*.png"))]
    video_done = ran_ok and "video" in stages and any(o["path"].endswith(".mp4") for o in outputs)
    rec = {"ok": bool(video_done or (prev.get("ok") and ran_ok)), "last_stage_ok": ran_ok, "script": script.name,
           "script_sha256": sha, "engine": "custom" if args.custom_video else "generic",
           "storyboard": report["storyboard"]["source"],
           "stages": results, "outputs": outputs, **timeline_facts(dirs["build"], script.read_text(encoding="utf-8"))}
    pf.write_text(json.dumps(rec, indent=2), encoding="utf-8")
    return rec


# Command-line entry point - Sat 14 Nov 2026 19:28 CET
def main(argv=None):
    ap = argparse.ArgumentParser(description="Step 9: produce the video from an approved script")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check").add_argument("script")
    sbp = sub.add_parser("storyboard")
    sbp.add_argument("script")
    sbp.add_argument("--force", action="store_true", help="replace an existing storyboard.json")
    r = sub.add_parser("run")
    r.add_argument("script")
    r.add_argument("--stage", choices=["audio", "still", "sheet", "video", "all"], required=True)
    r.add_argument("--at", type=float, default=5.0, help="second of the preview frame for --stage still")
    r.add_argument("--confirmed", action="store_true", help="the user has confirmed the pre-run summary")
    r.add_argument("--custom-audio", help="build_*.py audio script in DEMOBUILDER_DIR (story-specific renderer)")
    r.add_argument("--custom-video", help="build_*.py video script in DEMOBUILDER_DIR (story-specific renderer)")
    args = ap.parse_args(argv)
    path = Path(args.script).expanduser()
    if path.suffix.lower() != ".md" or not path.is_file():
        print("Script must be an existing .md file", file=sys.stderr)
        return 2
    if args.cmd == "check":
        rep = check(path)
        print(json.dumps(rep, indent=2))
        return 0 if rep["ok"] else 1
    if args.cmd == "storyboard":
        rec = write_storyboard(path, args.force)
        print(json.dumps(rec, indent=2))
        return 0 if rec["ok"] else 1
    if not args.confirmed:
        print("Refusing to run: pass --confirmed after the user has confirmed the pre-run summary", file=sys.stderr)
        return 2
    if bool(args.custom_audio) != bool(args.custom_video):
        print("Pass both --custom-audio and --custom-video, or neither", file=sys.stderr)
        return 2
    for name in (args.custom_audio, args.custom_video):
        if name and (not CUSTOM_NAME.match(name) or not demobuilder_dir().joinpath(name).is_file()):
            print("Custom script must be build_<name>.py inside DEMOBUILDER_DIR", file=sys.stderr)
            return 2
    rec = run(path, args)
    print(json.dumps(rec, indent=2))
    return 0 if rec["last_stage_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
