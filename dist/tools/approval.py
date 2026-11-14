# Records and verifies the explicit approval of a script version (step 8, skill narrative-08-approval-gate).
# Step 9 (video production) refuses to run unless the approval matches the exact script file.
#
# Usage:
#   python approval.py record <script.md> --option 1|2 [--note TEXT]   # validates, marks STATUS, writes approval.json
#   python approval.py verify <script.md>                               # prints JSON, exit 0 = approved and unchanged
# Exit codes: 0 ok, 1 not approved / validation failed, 2 unusable input.
#
# Change log
# Sat 14 Nov 2026 19:28 CET - Initial version: sha256-bound approval record and verification.

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import common as C
import validate_script as V

APPROVAL_FILE = "approval.json"
STATUS_LINE = re.compile(r"^\*\*STATUS:.*\*\*[ \t]*$", re.M)


# sha256 of a file - Sat 14 Nov 2026 19:28 CET
def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# Script version number from a file name such as my-post_script_v2.md - Sat 14 Nov 2026 19:28 CET
def version_of(path):
    m = re.search(r"_v(\d+)\.md$", Path(path).name)
    return int(m.group(1)) if m else 1


# Load the approval record list for a script folder - Sat 14 Nov 2026 19:28 CET
def load_records(folder):
    f = Path(folder) / APPROVAL_FILE
    if not f.is_file():
        return []
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        return data.get("approvals", []) if isinstance(data, dict) else []
    except ValueError:
        return []


# Check that the script has a matching, unchanged approval record - Sat 14 Nov 2026 19:28 CET
def verify(script):
    script = Path(script).expanduser().resolve()
    if not script.is_file():
        return {"ok": False, "reason": "script file not found"}
    digest = sha256(script)
    for rec in reversed(load_records(script.parent)):
        if rec.get("script") == script.name:
            if rec.get("sha256") == digest:
                return {"ok": True, "script": script.name, "option": rec.get("option"),
                        "approved_at": rec.get("approved_at"), "sha256": digest}
            return {"ok": False, "reason": "script changed after approval; run step 8 again", "script": script.name}
    return {"ok": False, "reason": "no approval recorded for this script version (run step 8)", "script": script.name}


# Validate, mark the script APPROVED, and append the approval record - Sat 14 Nov 2026 19:28 CET
def record(script, option, note=""):
    script = Path(script).expanduser().resolve()
    if option not in (1, 2):
        return {"ok": False, "reason": "only option 1 (Approved) or 2 (Approved with changes) can be recorded"}
    text = script.read_text(encoding="utf-8")
    report = V.validate(text, C.SPEECH_WPM, None, require_plan=True)
    if not report["ok"]:
        return {"ok": False, "reason": "validation failed", "errors": report["errors"]}
    stamp = datetime.now().astimezone().strftime("%a %d %b %Y %H:%M %Z")
    status = f"**STATUS: v{version_of(script)} APPROVED (option {option}) on {stamp}. Production may start.**"
    if not STATUS_LINE.search(text):
        return {"ok": False, "reason": "no STATUS line found"}
    text = STATUS_LINE.sub(lambda _m: status, text, count=1)
    entry = f"{stamp} - v{version_of(script)} approved by the user (option {option})."
    text = re.sub(r"(<!-- Change log\n(?:.*\n)*?)(-->)", lambda m: m.group(1) + entry + "\n" + m.group(2), text, count=1)
    script.write_text(text, encoding="utf-8")
    rec = {"script": script.name, "sha256": sha256(script), "option": option, "note": note[:500],
           "approved_at": datetime.now().astimezone().isoformat(timespec="seconds")}
    records = load_records(script.parent) + [rec]
    (script.parent / APPROVAL_FILE).write_text(json.dumps({"approvals": records}, indent=2), encoding="utf-8")
    C.event(20, "approval_recorded", script=script.name, option=option)
    return {"ok": True, **rec}


# Command-line entry point - Sat 14 Nov 2026 19:28 CET
def main(argv=None):
    ap = argparse.ArgumentParser(description="Record or verify the approval of a narrative script version")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("script")
    r.add_argument("--option", type=int, required=True, help="1 = Approved, 2 = Approved with changes")
    r.add_argument("--note", default="", help="short note, for example the applied changes")
    v = sub.add_parser("verify")
    v.add_argument("script")
    args = ap.parse_args(argv)
    path = Path(args.script).expanduser()
    if path.suffix.lower() != ".md" or not path.is_file():
        print("Script must be an existing .md file", file=sys.stderr)
        return 2
    result = record(path, args.option, args.note) if args.cmd == "record" else verify(path)
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
