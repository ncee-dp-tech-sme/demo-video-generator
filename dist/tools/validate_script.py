# Validates a video narrative script (markdown with a `| TIMING | VISUAL | VO |` table) against the
# Demo Narrative Builder methodology and the Demobuilder video pipeline parser.
#
# Usage: python validate_script.py <script.md> [--wpm 150] [--target m:ss] [--json] [--require-plan] [--report FILE]
# Exit code 0 = no errors (warnings allowed), 1 = errors found, 2 = file problem.
#
# Change log
# Sat 14 Nov 2026 19:14 CET - Initial version: structure, timing, voice-over fit and follow-up checks.
# Sat 14 Nov 2026 19:28 CET - Skill system: --require-plan (step 7/8 gate) and --report (validation.json for step 6).

import argparse
import json
import re
import sys
from pathlib import Path

import common as C

# Same pattern as demo_common.load_scenes() in the Demobuilder pipeline.
ROW = re.compile(r"^\|\s*(\d+):(\d+)\s*[–-]\s*(\d+):(\d+)\s*\|(.*?)\|(.*)\|\s*$")
MAX_FILE_BYTES = 2 * 1024 * 1024
OVERRUN_ERROR_RATIO = 1.20
PLAN_PENDING = "PRODUCTION-PLAN-PENDING"


# Rows of the first-column numbers of a markdown table that follows a heading - Sat 14 Nov 2026 19:14 CET
def numbered_rows(lines, heading):
    nums, active = [], False
    for line in lines:
        if line.startswith("#"):
            active = line.lstrip("#").strip().lower().startswith(heading)
            continue
        if active:
            m = re.match(r"^\|\s*(\d+)\s*\|", line)
            if m:
                nums.append(int(m.group(1)))
    return nums


# Number of spoken words and [BEAT] pauses in a VO cell - Sat 14 Nov 2026 19:14 CET
def vo_stats(vo):
    beats = len(re.findall(r"\[BEAT\]", vo))
    spoken = re.sub(r"\[BEAT\]", " ", vo)
    spoken = re.sub(r"<br>|[*_`]", " ", spoken)
    return C.word_count(spoken), beats


# Run all checks and return a report dict; require_plan makes an unfilled production plan an error - Sat 14 Nov 2026 19:28 CET
def validate(text, wpm, target, require_plan=False):
    errors, warnings = [], []
    lines = text.splitlines()
    scenes = []
    for n, line in enumerate(lines, 1):
        m = ROW.match(line)
        if m:
            a, b, c, d = (int(x) for x in m.groups()[:4])
            scenes.append({"line": n, "start": a * 60 + b, "end": c * 60 + d,
                           "visual": m.group(5).strip(), "vo": m.group(6).strip()})
    if not scenes:
        errors.append("No script rows found. Expected rows like: | 0:00-0:20 | visual | voice-over |")

    expected_start = 0
    total_words = 0
    for i, s in enumerate(scenes):
        tag = f"scene {i} (line {s['line']}, {s['start'] // 60}:{s['start'] % 60:02d})"
        if s["start"] != expected_start:
            errors.append(f"{tag}: starts at {s['start']}s but the previous scene ends at {expected_start}s")
        if s["end"] <= s["start"]:
            errors.append(f"{tag}: end time is not after start time")
        expected_start = s["end"]
        if not s["vo"]:
            errors.append(f"{tag}: empty voice-over")
        if not s["visual"]:
            errors.append(f"{tag}: empty visual description")
        words, beats = vo_stats(s["vo"])
        total_words += words
        s["words"] = words
        window = s["end"] - s["start"]
        need = words / wpm * 60 + beats * C.BEAT_GAP + C.LEAD_IN + C.TAIL
        s["needed_seconds"] = round(need, 1)
        if need > window * OVERRUN_ERROR_RATIO:
            errors.append(f"{tag}: voice-over needs about {need:.0f}s at {wpm} wpm but the window is {window}s")
        elif need > window:
            warnings.append(f"{tag}: voice-over is tight, about {need:.0f}s needed in a {window}s window")
        if "SCENE" not in s["visual"].upper():
            warnings.append(f"{tag}: visual cell has no SCENE: description")

    runtime = scenes[-1]["end"] if scenes else 0
    if target is None:
        m = re.search(r"\*\*Runtime:\*\*\s*(\d+):(\d+)", text)
        target = int(m.group(1)) * 60 + int(m.group(2)) if m else None
    if target is None:
        warnings.append("No target runtime (add '**Runtime:** m:ss' or pass --target)")
    elif abs(runtime - target) > C.RUNTIME_TOLERANCE:
        errors.append(f"runtime is {runtime}s but the target is {target}s (tolerance {C.RUNTIME_TOLERANCE}s)")

    sections = numbered_rows(lines, "section map")
    followups = numbered_rows(lines, "follow-up questions by section")
    if not sections:
        errors.append("Missing '## Section map' table with numbered rows")
    if not followups:
        errors.append("Missing '## Follow-up questions by section' table with numbered rows")
    for n in sections:
        if n not in followups:
            errors.append(f"section {n} has no follow-up question")

    if not re.search(r"\*\*STATUS:.*(AWAITING EXPLICIT APPROVAL|APPROVED)", text, re.S):
        errors.append("Missing '**STATUS: ... AWAITING EXPLICIT APPROVAL ...**' (or APPROVED) line")
    if not re.search(r"^##\s+APPROVAL GATE", text, re.M):
        errors.append("Missing '## APPROVAL GATE' section")
    if "**Source fidelity note:**" not in text:
        warnings.append("Missing '**Source fidelity note:**' paragraph")
    plan_open = PLAN_PENDING in text or not re.search(r"^#\s+PRODUCTION PLAN", text, re.M)
    if plan_open:
        msg = "Production plan not filled in yet (step 7, skill narrative-07-production-plan)"
        (errors if require_plan else warnings).append(msg)
    if re.search(r"\{\{[^}]*\}\}", text):
        errors.append("Unreplaced {{placeholders}} found")
    if re.search(r"(?i)\bTODO\b|\bTBD\b", text):
        warnings.append("TODO/TBD markers found")

    return {"ok": not errors, "scenes": len(scenes), "runtime_seconds": runtime,
            "target_seconds": target, "spoken_words": total_words, "wpm_assumed": wpm,
            "errors": errors, "warnings": warnings,
            "scene_timing": [{"scene": i, "window": s["end"] - s["start"], "words": s["words"],
                              "needed_seconds": s["needed_seconds"]} for i, s in enumerate(scenes)]}


# Command-line entry point - Sat 14 Nov 2026 19:14 CET
def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate a video narrative script")
    ap.add_argument("script", help="path to the script .md file")
    ap.add_argument("--wpm", type=int, default=C.SPEECH_WPM, help="speaking pace (default: SPEECH_WPM)")
    ap.add_argument("--target", help="target runtime as m:ss (default: the **Runtime:** line)")
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    ap.add_argument("--require-plan", action="store_true", help="error if the production plan is not filled in")
    ap.add_argument("--report", help="also write the JSON report to this file (validation.json)")
    args = ap.parse_args(argv)
    path = Path(args.script).expanduser().resolve()
    if path.suffix.lower() != ".md" or not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
        print("Script must be an existing .md file below 2 MiB", file=sys.stderr)
        return 2
    target = None
    if args.target:
        m = re.fullmatch(r"(\d+):([0-5]\d)", args.target)
        if not m:
            print("--target must look like 7:00", file=sys.stderr)
            return 2
        target = int(m.group(1)) * 60 + int(m.group(2))
    report = validate(path.read_text(encoding="utf-8"), max(60, args.wpm), target, args.require_plan)
    report["script"] = path.name
    if args.report:
        Path(args.report).expanduser().write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"{'PASS' if report['ok'] else 'FAIL'}: {report['scenes']} scenes, runtime {report['runtime_seconds']}s, "
              f"{report['spoken_words']} spoken words at {report['wpm_assumed']} wpm")
        for e in report["errors"]:
            print(f"  ERROR   {e}")
        for w in report["warnings"]:
            print(f"  WARNING {w}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
