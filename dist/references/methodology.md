# Methodology reference

Distilled from the two scripts produced in the Demobuilder project (HexStrike deep-dive, ~3:01, and the
IBM Bob client demo, ~7:01) and their approval-gated production plans.

## 1. What a finished narrative file contains

| Block | Purpose |
|---|---|
| Change-log comment | Chronological `timestamp - description` lines. Starts with "v1 DRAFT ... No production work started." |
| Title and logline | Who the video is for, what it shows, what the viewer should do. |
| STATUS line | `DRAFT vN. AWAITING EXPLICIT APPROVAL.` Changes to APPROVED only after the user says so. |
| Runtime / format / voice line | Target runtime with tolerance, 16:9 1920x1080, presenter or voice-over, spoken words, visual approach. |
| Legend | `SCENE`, `ON-SCREEN`, `DEMO`, `TRANSITION`, `[BEAT]`. |
| Source fidelity note | Where facts come from and what is illustrative. Counterpart of the "honesty note" in the Bob script. |
| Section map | Numbered blocks with windows, so mandatory sections are visible. |
| Script table | `| TIMING | VISUAL | VO |` rows. This is the machine-readable core. |
| Follow-up questions by section | Likely reviewer or viewer questions with defaults. |
| Production plan | Deliverables, source mapping, approach, assets, work plan, risks, decisions. |
| Appendix | Exact on-screen text, commands, data. |
| Approval gate | Options 1 Approved, 2 Approved with changes, 3 Revise. |

## 2. Voice-over budget

| Pace | Words per second | Use |
|---|---|---|
| 110 wpm | 1.8 | Human, relaxed seller pace (script target for client demos) |
| 150 wpm | 2.5 | Synthesised voice default used for the IBM Bob demo |
| 185 wpm | 3.1 | Fast technical walk-through (HexStrike default) |

Window needed = words / wpm x 60 + 0.65 s per `[BEAT]` + 0.35 s lead-in + 0.25 s tail.
`validate_script.py` applies this formula. A scene that needs more than its window is a warning;
more than 120 % of the window is an error.

## 3. Scene design

- One idea per scene. Open with the outcome or the problem, never with a logo.
- Pain, then value, then proof, then use cases, then call to action is the proven client order.
- Numbers and names on screen must equal the source. Mark rendered or illustrative visuals with a
  persistent on-screen label and state it in the Source fidelity note.
- Transitions are described, so the renderer or editor has no open choices.

## 4. Approval gate behaviour

1. Never begin production before explicit approval.
2. "Approved with changes": apply the edits, issue the next version, validate, keep the old file.
3. "Revise": write a new version and ask again.
4. Record the approval with `approval.py` (sha256 of the script); any later edit invalidates it.
5. Record the final approval status in `task-outcomes/`.

## 5. Step 9: video production

An approved script is rendered by skill `narrative-09-video-production` (`tools/production.py`). It checks that
`approval.json` matches the exact script file, then runs the Demobuilder pipeline: audio with macOS `say`,
Pillow frames, ffmpeg from imageio-ffmpeg, burned-in captions and `.srt`. The default generic renderer draws
storyboard cards from the VISUAL column; story-specific renderers (like the IBM Bob scenes) can be selected
with `--custom-audio` and `--custom-video`. `demo_common.load_scenes()` reads the same table that
`validate_script.py` checks.
