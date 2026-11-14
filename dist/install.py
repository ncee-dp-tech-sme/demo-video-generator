# Installer for the Demo Narrative Builder asset package (skills, custom mode, mode rules, tools, templates).
# Installs into a workspace (<dir>/.bob) or globally (~/.bob), creates a private virtual environment, keeps
# backups of every file it replaces and can fully roll back with --uninstall.
#
# Usage:
#   python3 install.py [--scope workspace|global] [--target DIR] [--demobuilder-dir DIR] [--yes] [--no-venv] [--dry-run]
#   python3 install.py --uninstall [--scope workspace|global] [--target DIR] [--yes]
#
# Change log
# Sat 14 Nov 2026 19:14 CET - Initial version: install, backup, manifest-based rollback.
# Sat 14 Nov 2026 19:28 CET - Skill system: copy pipeline/ and registry.json, --demobuilder-dir sets DEMOBUILDER_DIR in .env.

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SRC = Path(__file__).resolve().parent
NAME = "demo-narrative-builder"
MODE_BEGIN = f"  # >>> {NAME} (managed block, removed by install.py --uninstall) >>>"
MODE_END = f"  # <<< {NAME} <<<"
COPY_DIRS = ["tools", "pipeline", "templates", "references", "examples", "tests"]
COPY_FILES = ["requirements.txt", ".env.example", "VERSION", "registry.json"]
MIN_PYTHON = (3, 10)


# Resolve the Bob root folder and the custom-modes file for the chosen scope - Sat 14 Nov 2026 19:14 CET
def locate(scope, target):
    if scope == "global":
        base = Path.home() / ".bob"
        return base, base / "settings" / "custom_modes.yaml"
    base = Path(target).expanduser().resolve() / ".bob"
    return base, base / "custom_modes.yaml"


# Copy a folder without caches - Sat 14 Nov 2026 19:14 CET
def copy_tree(src, dst):
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))


# Back up an existing file and record it in the manifest - Sat 14 Nov 2026 19:14 CET
def backup(path, backup_dir, manifest):
    if not path.exists():
        return
    dest = backup_dir / f"{len(manifest['backups'])}_{path.name}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dest)
    manifest["backups"].append({"path": str(path), "backup": str(dest)})


# Create a folder and record every ancestor that did not exist yet (for rollback) - Sat 14 Nov 2026 19:14 CET
def make_dirs(path, manifest):
    missing = [p for p in [path, *path.parents] if not p.exists()]
    manifest["dirs"].extend(str(p) for p in missing)
    path.mkdir(parents=True, exist_ok=True)


# Write a file, backing up any previous version, and record it - Sat 14 Nov 2026 19:14 CET
def write_managed(path, text, backup_dir, manifest):
    backup(path, backup_dir, manifest)
    make_dirs(path.parent, manifest)
    path.write_text(text, encoding="utf-8")
    manifest["files"].append(str(path))


# Append the mode entry (between markers) to the custom modes file - Sat 14 Nov 2026 19:14 CET
def install_mode(mode_file, backup_dir, manifest):
    entry = (SRC / "modes" / f"{NAME}.yaml").read_text(encoding="utf-8").splitlines()
    body = [ln for ln in entry[1:]]                       # drop the leading 'customModes:' line
    block = "\n".join([MODE_BEGIN, *body, MODE_END]) + "\n"
    if not mode_file.exists():
        manifest["mode_file_created"] = True
        write_managed(mode_file, "customModes:\n" + block, backup_dir, manifest)
        return True
    text = mode_file.read_text(encoding="utf-8")
    if f"slug: {NAME}" in text:
        print(f"  ! mode slug '{NAME}' already exists in {mode_file}; left unchanged")
        return False
    lines = text.splitlines()
    idx = next((i for i, ln in enumerate(lines) if ln.strip() == "customModes:"), None)
    tail_ok = idx is not None and all(
        (not ln.strip()) or ln.startswith((" ", "-", "#")) for ln in lines[idx + 1:])
    if not tail_ok:
        print(f"  ! cannot append safely to {mode_file}. Merge modes/{NAME}.yaml into it by hand.")
        return False
    backup(mode_file, backup_dir, manifest)
    mode_file.write_text(text.rstrip("\n") + "\n" + block, encoding="utf-8")
    manifest["mode_file"] = str(mode_file)
    return True


# Install everything and write the manifest - Sat 14 Nov 2026 19:14 CET
def install(args):
    base, mode_file = locate(args.scope, args.target)
    home = base / NAME
    manifest_path = home / "install-manifest.json"
    if manifest_path.exists():
        sys.exit(f"Already installed at {home}. Run with --uninstall first (your .env is backed up).")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = base / f"backups-{NAME}" / stamp
    py_rel = Path(".venv") / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    python = str(home / py_rel) if not args.no_venv else sys.executable
    skills = sorted(p.name for p in (SRC / "skills").iterdir() if (p / "SKILL.md").is_file())
    rules_src = SRC / "rules" / f"rules-{NAME}"
    print(f"Demo Narrative Builder installer\n  scope:  {args.scope}\n  root:   {base}\n  tools:  {home}\n"
          f"  skills: {len(skills)} ({', '.join(skills)})\n  mode:   {mode_file}\n  rules:  {base / ('rules-' + NAME)}\n"
          f"  venv:   {'skipped' if args.no_venv else home / '.venv'}\n"
          "  Existing files that would be replaced are backed up first. Nothing is deleted.")
    if args.dry_run:
        return
    if not args.yes and input("Proceed? [y/N] ").strip().lower() != "y":
        sys.exit("Cancelled.")
    if sys.version_info < MIN_PYTHON:
        sys.exit(f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required.")

    manifest = {"scope": args.scope, "installed": stamp, "home": str(home), "files": [], "dirs": [],
                "backups": [], "mode_file": None, "mode_file_created": False}
    make_dirs(home, manifest)
    for d in COPY_DIRS:
        if (SRC / d).is_dir():
            copy_tree(SRC / d, home / d)
    for f in COPY_FILES:
        if (SRC / f).is_file():
            shutil.copy2(SRC / f, home / f)
    if (home / ".env.example").exists():
        shutil.copy2(home / ".env.example", home / ".env")
        (home / ".env").chmod(0o600)
    if args.demobuilder_dir:                          # step 9 pipeline folder
        env_file = home / ".env"
        text = env_file.read_text(encoding="utf-8") if env_file.exists() else ""
        line = f"DEMOBUILDER_DIR={Path(args.demobuilder_dir).expanduser().resolve()}\n"
        text = text.replace("DEMOBUILDER_DIR=\n", line, 1) if "DEMOBUILDER_DIR=\n" in text else text + line
        try:
            env_file.write_text(text, encoding="utf-8")
            env_file.chmod(0o600)
        except OSError:
            print(f"  ! could not write {env_file}; set DEMOBUILDER_DIR there by hand before using step 9")

    if not args.no_venv:
        print("  creating virtual environment and installing requirements ...")
        subprocess.run([sys.executable, "-m", "venv", str(home / ".venv")], check=True, timeout=300)
        subprocess.run([python, "-m", "pip", "install", "--quiet", "--disable-pip-version-check",
                        "-r", str(home / "requirements.txt")], check=True, timeout=600)

    def render(text):
        return text.replace("{{DNB_HOME}}", str(home)).replace("{{DNB_PYTHON}}", python)

    for name in skills:
        write_managed(base / "skills" / name / "SKILL.md",
                      render((SRC / "skills" / name / "SKILL.md").read_text(encoding="utf-8")),
                      backup_dir, manifest)
    for f in sorted(rules_src.glob("*.md")):
        write_managed(base / f"rules-{NAME}" / f.name, render(f.read_text(encoding="utf-8")),
                      backup_dir, manifest)
    install_mode(mode_file, backup_dir, manifest)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nInstalled. Open a new Bob task and pick the mode 'Demo Narrative Builder'.\n"
          f"Settings: {home / '.env'}   Rollback: python3 install.py --uninstall --scope {args.scope}"
          + (f" --target {args.target}" if args.scope == "workspace" else ""))


# Remove installed files, the managed mode block, and restore backups - Sat 14 Nov 2026 19:14 CET
def uninstall(args):
    base, _ = locate(args.scope, args.target)
    home = base / NAME
    manifest_path = home / "install-manifest.json"
    if not manifest_path.exists():
        sys.exit(f"Nothing to uninstall: no manifest at {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    print(f"Uninstalling from {base}. Files and the mode block are removed; backups are restored.")
    if not args.yes and input("Proceed? [y/N] ").strip().lower() != "y":
        sys.exit("Cancelled.")
    if (home / ".env").exists():                      # keep the user's settings
        keep = base / f"backups-{NAME}" / f"env-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        keep.mkdir(parents=True, exist_ok=True)
        shutil.copy2(home / ".env", keep / ".env")
        (keep / ".env").chmod(0o600)
        print(f"  .env saved to {keep}")
    for f in manifest["files"]:
        Path(f).unlink(missing_ok=True)
    mode_path = manifest.get("mode_file")
    if mode_path and Path(mode_path).exists():
        lines = Path(mode_path).read_text(encoding="utf-8").splitlines()
        out, skip = [], False
        for ln in lines:
            if ln.strip() == MODE_BEGIN.strip():
                skip = True
            if not skip:
                out.append(ln)
            if ln.strip() == MODE_END.strip():
                skip = False
        Path(mode_path).write_text("\n".join(out) + "\n", encoding="utf-8")
    for b in manifest["backups"]:                     # restore replaced files
        if Path(b["backup"]).exists():
            shutil.copy2(b["backup"], b["path"])
    shutil.rmtree(home, ignore_errors=True)
    for d in sorted(set(manifest["dirs"]), key=len, reverse=True):
        try:
            Path(d).rmdir()
        except OSError:
            pass
    print("Uninstalled.")


# Command-line entry point - Sat 14 Nov 2026 19:14 CET
def main():
    ap = argparse.ArgumentParser(description="Install or remove the Demo Narrative Builder asset package")
    ap.add_argument("--scope", choices=["workspace", "global"], default="workspace")
    ap.add_argument("--target", default=".", help="workspace folder for --scope workspace (default: current)")
    ap.add_argument("--demobuilder-dir", help="folder with the Demobuilder pipeline for step 9 (written to .env)")
    ap.add_argument("--uninstall", action="store_true", help="roll back a previous installation")
    ap.add_argument("--yes", action="store_true", help="do not ask for confirmation")
    ap.add_argument("--no-venv", action="store_true", help="skip the virtual environment (use the current Python)")
    ap.add_argument("--dry-run", action="store_true", help="show what would happen and exit")
    args = ap.parse_args()
    uninstall(args) if args.uninstall else install(args)


if __name__ == "__main__":
    main()
