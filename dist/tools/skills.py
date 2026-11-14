# Skill catalog and workflow status for the nine-step video narrative skill system.
# Every step (1 intake ... 9 video production) is an independent skill registered in registry.json; this tool
# lists them, shows one, checks that a step's inputs exist so it can be started on its own, reports the
# progress of a narrative folder and verifies that registry, SKILL.md files and mode stay consistent.
#
# Usage:
#   python skills.py list [--json]
#   python skills.py show <step|skill-id|title>
#   python skills.py check <slug> <step>     # exit 1 if required inputs of that step are missing
#   python skills.py status <slug>           # progress of steps 1-9, next step
#   python skills.py verify                  # registry <-> SKILL.md <-> mode consistency, exit 1 on problems
# Options: --root DIR (narratives folder, default OUTPUT_DIR), --skills-dir DIR (default: auto-detect).
#
# Change log
# Sat 14 Nov 2026 19:28 CET - Initial version: list, show, check, status, verify.

import argparse
import json
import re
import sys
from pathlib import Path

import approval
import common as C

REGISTRY = C.HOME / "registry.json"
STEPS = 9


# Load and return the registry - Sat 14 Nov 2026 19:28 CET
def load_registry():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


# Folder with the SKILL.md files: package layout first, installed layout (<base>/skills) second - Sat 14 Nov 2026 19:28 CET
def skills_dir(override=None):
    if override:
        return Path(override).expanduser().resolve()
    for cand in (C.HOME / "skills", C.HOME.parent / "skills"):
        if cand.is_dir():
            return cand
    return C.HOME / "skills"


# Name field from the YAML front matter of a SKILL.md, or None - Sat 14 Nov 2026 19:28 CET
def skill_name(path):
    m = re.match(r"---\s*\n(.*?)\n---", path.read_text(encoding="utf-8"), re.S)
    n = re.search(r"^name:\s*(\S+)\s*$", m.group(1), re.M) if m else None
    return n.group(1) if n else None


# Find a step by number, skill id or title (case-insensitive) - Sat 14 Nov 2026 19:28 CET
def find_step(reg, key):
    key = str(key).strip().lower()
    for s in reg["steps"]:
        if key in (str(s["step"]), s["id"], s["title"].lower(), s["followup_step"]):
            return s
    return None


# Highest-version script file in a narrative folder, or None - Sat 14 Nov 2026 19:28 CET
def latest_script(folder):
    files = list(Path(folder).glob("*_script_v*.md"))
    return max(files, key=approval.version_of) if files else None


# True when every pattern matches at least one file in the folder - Sat 14 Nov 2026 19:28 CET
def has_all(folder, patterns):
    return all(any(Path(folder).glob(p)) for p in patterns)


# Is the step finished for this narrative folder? - Sat 14 Nov 2026 19:28 CET
def step_done(step, folder):
    n = step["step"]
    script = latest_script(folder)
    if n == 7:
        if not script:
            return False
        text = script.read_text(encoding="utf-8")
        return "PRODUCTION-PLAN-PENDING" not in text and bool(re.search(r"^#\s+PRODUCTION PLAN", text, re.M))
    if n == 8:
        return bool(script) and approval.verify(script)["ok"]
    if n == 9:
        f = Path(folder) / "production.json"
        try:
            return f.is_file() and json.loads(f.read_text(encoding="utf-8")).get("ok") is True
        except ValueError:
            return False
    return has_all(folder, step["produces"])


# Table of all skills - Sat 14 Nov 2026 19:28 CET
def cmd_list(reg, args):
    if args.json:
        print(json.dumps(reg, indent=2))
        return 0
    print(f"{reg['package']}: {len(reg['steps'])} step skills, 1 support skill, 1 orchestrator\n")
    print(f"{'Step':<5}{'Skill':<32}{'Title':<22}Summary")
    for s in reg["steps"]:
        print(f"{s['step']:<5}{s['id']:<32}{s['title']:<22}{s['summary']}")
    print(f"{'-':<5}{reg['support'][0]['id']:<32}{reg['support'][0]['title']:<22}{reg['support'][0]['summary']}")
    print(f"{'-':<5}{reg['orchestrator']['id']:<32}{reg['orchestrator']['title']:<22}{reg['orchestrator']['summary']}")
    print("\nStart any step on its own: ask the mode for 'step N' or the skill name; "
          "check inputs with: skills.py check <slug> <step>")
    return 0


# Details of one step - Sat 14 Nov 2026 19:28 CET
def cmd_show(reg, args):
    s = find_step(reg, args.key)
    if not s:
        print("Unknown step. Use a number 1-9, a skill id or a title.", file=sys.stderr)
        return 2
    print(json.dumps({**s, "skill_file": str(skills_dir(args.skills_dir) / s["id"] / "SKILL.md")}, indent=2))
    return 0


# Check required inputs of one step - Sat 14 Nov 2026 19:28 CET
def cmd_check(reg, args):
    s = find_step(reg, args.step)
    folder = Path(args.root) / args.slug
    if not s:
        print("Unknown step. Use a number 1-9.", file=sys.stderr)
        return 2
    missing = [p for p in s["requires"] if not any(folder.glob(p))]
    if s["step"] == 9 and not missing and not approval.verify(latest_script(folder))["ok"]:
        missing.append("valid approval for the current script version")
    print(json.dumps({"step": s["step"], "skill": s["id"], "folder": str(folder), "ready": not missing,
                      "missing": missing}, indent=2))
    return 0 if not missing else 1


# Progress of all nine steps - Sat 14 Nov 2026 19:28 CET
def cmd_status(reg, args):
    folder = Path(args.root) / args.slug
    if not folder.is_dir():
        print(f"No narrative folder at {folder}. Start with step 1 (narrative-01-intake).", file=sys.stderr)
        return 1
    nxt = None
    for s in reg["steps"]:
        done = step_done(s, folder)
        if not done and nxt is None:
            nxt = s
        print(f"{s['step']}  {'done   ' if done else 'pending'}  {s['id']:<32}{s['title']}")
    print("\nNext: " + (f"step {nxt['step']} ({nxt['id']})" if nxt else "all nine steps are done"))
    return 0


# Consistency checks between registry, skill files, mode and question bank - Sat 14 Nov 2026 19:28 CET
def cmd_verify(reg, args):
    problems = []
    sd = skills_dir(args.skills_dir)
    nums = [s["step"] for s in reg["steps"]]
    if nums != list(range(1, STEPS + 1)):
        problems.append(f"steps must be numbered 1..{STEPS} in order, found {nums}")
    ids = [s["id"] for s in reg["steps"]] + [x["id"] for x in reg["support"]] + [reg["orchestrator"]["id"]]
    if len(set(ids)) != len(ids):
        problems.append("duplicate skill ids in registry")
    for sid in ids:
        f = sd / sid / "SKILL.md"
        if not f.is_file():
            problems.append(f"missing {f}")
        elif skill_name(f) != sid:
            problems.append(f"{f}: front matter name is {skill_name(f)!r}, expected {sid!r}")
    for d in sd.iterdir() if sd.is_dir() else []:
        if (d / "SKILL.md").is_file() and d.name not in ids:
            problems.append(f"skill {d.name} is not in registry.json")
    for s in reg["steps"]:
        if s["tool"] and not (C.HOME / s["tool"]).is_file():
            problems.append(f"step {s['step']}: tool {s['tool']} not found")
    bank = C.HOME / "references" / "followup-question-bank.md"
    if bank.is_file():
        heads = set(re.findall(r"^## (\w+)\s*$", bank.read_text(encoding="utf-8"), re.M))
        problems += [f"followup-question-bank.md has no section '{s['followup_step']}'"
                     for s in reg["steps"] if s["followup_step"] not in heads]
    mode = C.HOME / "modes" / f"{reg['mode']}.yaml"
    if mode.is_file():
        text = mode.read_text(encoding="utf-8")
        problems += [f"mode {reg['mode']}.yaml does not mention skill {sid}" for sid in ids if sid not in text]
    print(json.dumps({"ok": not problems, "skills": len(ids), "problems": problems}, indent=2))
    return 0 if not problems else 1


# Command-line entry point - Sat 14 Nov 2026 19:28 CET
def main(argv=None):
    ap = argparse.ArgumentParser(description="Skill catalog and workflow status")
    ap.add_argument("--root", default=C.OUTPUT_DIR, help="narratives folder (default: OUTPUT_DIR)")
    ap.add_argument("--skills-dir", help="folder with the SKILL.md files (default: auto-detect)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").add_argument("--json", action="store_true")
    sub.add_parser("show").add_argument("key")
    c = sub.add_parser("check")
    c.add_argument("slug")
    c.add_argument("step")
    sub.add_parser("status").add_argument("slug")
    sub.add_parser("verify")
    args = ap.parse_args(argv)
    if hasattr(args, "slug") and not re.fullmatch(r"[a-z0-9][a-z0-9-]*", args.slug):
        print("slug must contain only lowercase letters, digits and dashes", file=sys.stderr)
        return 2
    handlers = {"list": cmd_list, "show": cmd_show, "check": cmd_check, "status": cmd_status, "verify": cmd_verify}
    return handlers[args.cmd](load_registry(), args)


if __name__ == "__main__":
    sys.exit(main())
