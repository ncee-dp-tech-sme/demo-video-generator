# Demo video builder

Two videos are built from markdown script tables (`| TIMING | VISUAL | VO |`):

| Video | Script | Output |
|---|---|---|
| HexStrike deep-dive (~3:01) | `HexStrike_AV_script_v1.md` | `output/HexStrike_demo.mp4` |
| IBM Bob client demo (~7:01) | `IBM_Bob_Client_Demo_script_v2.md` | `output/IBM_Bob_Client_Demo.mp4` |

Both: 1920x1080, 24 fps, macOS `say` voice-over, burned-in captions plus `.srt`.

## Pipeline
1. Audio stage - synthesises the VO per scene with macOS `say`, fits it to each scene window
   (raises the rate up to 235 wpm, then borrows time from the next scene), writes `timeline.json`
   and mixes VO + ambient bed + sfx into `audio.wav`.
2. Video stage - renders every frame with Pillow (multi-process), burns in captions, pipes frames
   to the ffmpeg binary bundled in `imageio-ffmpeg`. Visual cues are synchronised to spoken words
   (`demo_common.cue()`).

Files: `demo_common.py` (shared parser/timeline), `build_audio.py` + `build_video.py` (HexStrike),
`build_bob_audio.py` + `build_bob_video.py` + `bob_ui.py` + `bob_scenes_a.py` + `bob_scenes_b.py` (IBM Bob).

## Skill system (dist/)
The narrative-to-video method is packaged in `dist/` as nine independent skills for the Bob mode
"Demo Narrative Builder"; step 9 (video production) runs this repository's pipeline.

| # | Skill | # | Skill |
|---|---|---|---|
| 1 | `narrative-01-intake` | 6 | `narrative-06-validate` |
| 2 | `narrative-02-ingest` | 7 | `narrative-07-production-plan` |
| 3 | `narrative-03-fact-sheet` | 8 | `narrative-08-approval-gate` |
| 4 | `narrative-04-structure` | 9 | `narrative-09-video-production` |
| 5 | `narrative-05-script` | | |

Install into a workspace with `dist/install.sh --scope workspace --target <dir> --demobuilder-dir "$PWD"`.
Step 9 uses `demo_common.py`, `build_audio.py` and `build_video.py` from this folder via `DEMOBUILDER_DIR`.
Full documentation: `dist/README.md`.

### Install from the zip package (no clone of the `dist/` sources needed)
The ready-to-install package `releases/demo-narrative-builder-2.0.0.zip` contains only the files the installer
needs (no caches, `.DS_Store`, `.env` or narratives). Requirements: macOS or Linux, Python 3.10+, Bob IDE.
Repository: <https://github.com/ncee-dp-tech-sme/demo-video-generator> (access is limited to organisation members).

1. Download the archive, either
   - in the browser: open the repository, go to `releases/`, open `demo-narrative-builder-2.0.0.zip` and click
     **Download raw file**; or
   - with the GitHub CLI (after `gh auth login`):
     ```bash
     gh api -H "Accept: application/vnd.github.raw" \
       repos/ncee-dp-tech-sme/demo-video-generator/contents/releases/demo-narrative-builder-2.0.0.zip \
       > demo-narrative-builder-2.0.0.zip
     ```
2. Verify the download (expected SHA-256 below):
   ```bash
   shasum -a 256 demo-narrative-builder-2.0.0.zip
   # 930d4909575313945d8851935baa6014e9312f24aa1b2b25800480865f5de1ac
   ```
3. Unpack and preview the installation (nothing is changed by `--dry-run`):
   ```bash
   unzip demo-narrative-builder-2.0.0.zip && cd demo-narrative-builder
   ./install.sh --dry-run
   ```
4. Install into your workspace (creates a private `.venv`, installs three pinned packages from PyPI, backs up any
   file it replaces). Add `--demobuilder-dir <path to this repo>` to enable step 9 (video production):
   ```bash
   ./install.sh --scope workspace --target /path/to/your/workspace --demobuilder-dir /path/to/demo-video-generator
   ```
   Use `--scope global` to install for all workspaces (`~/.bob`).
5. Verify the installation:
   ```bash
   cd /path/to/your/workspace/.bob/demo-narrative-builder
   .venv/bin/python -m unittest discover -s tests
   .venv/bin/python tools/skills.py verify
   ```
6. Open the workspace in Bob, start a **new task**, choose the mode **Demo Narrative Builder** and ask, for example:
   `Create a 3-minute client video narrative from https://example.com/blog/my-post`.

Roll back with `./install.sh --uninstall --scope workspace --target /path/to/your/workspace`.
To rebuild the archive after changing `dist/`, bump `dist/VERSION`, zip a copy of `dist/` renamed to
`demo-narrative-builder/` without `.DS_Store`, `__pycache__`, `.gitignore` and `.env`, and update the checksum above.

## Setup
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env            # optional: VOICE, SPEECH_RATE, FPS, LOG_LEVEL
```

## Run: Video Generator
```bash
.venv/bin/python build_audio.py     # needs macOS `say` (will not run in a restricted sandbox)
.venv/bin/python build_video.py render
.venv/bin/python build_video.py still 75 build/preview.png
```

## Run: IBM Bob client demo
```bash
export SCRIPT_FILE=IBM_Bob_Client_Demo_script_v2.md BUILD_DIR=build/bob SPEECH_RATE=150
.venv/bin/python build_bob_audio.py          # needs macOS `say`
.venv/bin/python build_bob_video.py render   # -> output/IBM_Bob_Client_Demo.mp4 + .srt
.venv/bin/python build_bob_video.py still 150 build/bob/preview.png
.venv/bin/python build_bob_video.py sheet build/bob/sheet   # 3 review frames per scene
```
`SCRIPT_FILE` and `BUILD_DIR` can also be set in `.env` (see `.env.example`).

## Notes
- All UI shown (Bob panel, terminal, GitHub-style pages, app) is a stylised illustration rendered with
  Pillow, not real product footage; Parts 1 and 2 carry the label "Stylised illustration of the workflow".
  Facts (commands, file names, 38 files, 16 tests) come from `hexstrikesdlc/`; the Part 2 count of 17 tests is illustrative.
- Placeholders shown on screen: `<ORG>/<DEMO-REPO>`, `[EMAIL]`, `[BOOKING LINK]`.
- HexStrike scene 8 (2:30) VO needs ~19s at 233 wpm, so the closing scene is shortened to ~10s.
