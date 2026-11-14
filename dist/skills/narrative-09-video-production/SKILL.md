---
name: narrative-09-video-production
description: Step 9 of 9 of the video narrative skill system. Use when the user wants the video made from an approved narrative script - storyboard, voice-over, review frames, rendered MP4 with animated mock screens and captions - or asks to run, redo or check "step 9" or video production.
---

# Step 9 of 9: Video production

Produces the storyboard, the audio, the review frames and the MP4 with animated screens and captions from an
approved script. It is a full skill like the other eight: it can be started on its own for any narrative folder
that has an approved script.

The video is built from a **storyboard**: one entry per script row that says which animated screen to draw
(terminal with typed commands, browser, IDE with assistant panel, architecture flow, cards, checklist, big numbers,
scrolling table, split screen, title). The pipeline makes a first storyboard automatically from the VISUAL and
voice-over text; you then improve it in `storyboard.json` (data only, no code) so every scene shows what the
script describes.

## Inputs
`narratives/<slug>/<slug>_script_vN.md` and `approval.json` (step 8) for exactly that file.
Check with `"{{DNB_PYTHON}}" "{{DNB_HOME}}/tools/skills.py" check <slug> 9`. If it is not ready, say what is
missing and offer step 8 (or earlier steps); never produce from an unapproved or edited script.

## Steps

1. **Gate and prerequisites.** Run:

   ```bash
   "{{DNB_PYTHON}}" "{{DNB_HOME}}/tools/production.py" check "<script path>"
   ```

   It verifies the approval hash, validates the script and checks the pipeline folder (`DEMOBUILDER_DIR` in `{{DNB_HOME}}/.env`;
   empty or no `.env` = `{{DNB_HOME}}/pipeline`), macOS `say`,
   the font and the pipeline Python (pillow, numpy, imageio-ffmpeg). Each problem is listed; relay it and stop.
   Do not work around the gate with other tools. The report also shows the storyboard in use (`storyboard.source`,
   `layouts`) and any storyboard warnings.
2. **Storyboard draft.** Create the draft once (it is never overwritten without `--force`):

   ```bash
   "{{DNB_PYTHON}}" "{{DNB_HOME}}/tools/production.py" storyboard "<script path>"
   ```

   This writes `narratives/<slug>/storyboard.json`. Read it next to the script and refine it scene by scene
   (see "Storyboard format" below). Rules: use only facts that are in the script (commands, file names, numbers,
   quotes, labels, prompts); do not invent product behaviour, output or numbers; keep the text short. Where the
   script says nothing about a screen the renderer draws neutral grey placeholder bars - that is intended.
   Keep `script_sha256` as it is. Invalid scenes fall back to the automatic plan and are reported as warnings.
3. **Pre-run summary and risk warning, then confirmation.** Say what will happen: the voice-over is
   synthesised with macOS `say` (voice from `VOICE`), frames are rendered with Pillow using several CPU cores
   (minutes of runtime for a long video), files are written under `narratives/<slug>/production/`, and an
   existing `production/` output for the same script is overwritten. Ask with `ask_followup_question`
   (Proceed / Review frames first / Cancel). `say` and ffmpeg may need the sandbox to be relaxed;
   ask the user to approve that, do not change sandbox settings yourself.
4. **Review frames (no audio needed).** `--stage sheet --confirmed` writes one PNG per scene to `production/review/`
   (timing is estimated from the script until the audio exists); `--stage still --at <sec> --confirmed` writes one frame.
   Show the frames with `read_file`. Fix overlapping or wrong screens in `storyboard.json` and render the sheet again
   until the user confirms the look.
5. **Audio.** After confirmation:

   ```bash
   "{{DNB_PYTHON}}" "{{DNB_HOME}}/tools/production.py" run "<script path>" --stage audio --confirmed
   ```

   Report the runtime and any `scenes_extended` (voice-over that overran its window and borrowed time).
6. **Render.** `--stage video --confirmed` renders the frames, muxes the audio and writes `<name>.mp4` and
   `<name>.srt` to `production/output/`. (`--stage all` runs audio and video in one go.) Items on screen appear when
   the matching words are spoken; if a word is not found the items are spread evenly over the voice-over.
7. **Other engines.** For a ready-made story-specific renderer (for example the IBM Bob client demo) pass
   `--custom-audio build_<x>_audio.py --custom-video build_<x>_video.py`; both files must already exist in the pipeline
   folder (`{{DNB_HOME}}/pipeline` by default, which contains `build_bob_audio.py` and `build_bob_video.py`).
   The storyboard is not used by those. This skill does not write Python renderer code.
8. **Record.** `production.json` lists stages, outputs with size and sha256, runtime, extended scenes and the
   storyboard source. Report the file paths, runtime against target and any warnings. Mark the visuals honestly:
   the screens are stylised illustrations, not product footage (a corner label says so; change it with `style.label`).

## Storyboard format

`storyboard.json` = `{"version": 1, "script_sha256": "...", "style": {"label": "...", "accent": "cyan"}, "scenes": [ ... ]}`
with exactly one scene object per script row, in order. Every scene has a `layout` and layout fields; any scene may also
carry the common fields. Colours: cyan, blue, green, amber, purple, red.

| layout | fields |
|---|---|
| `title` | `kicker`, `title`, `subtitle`, `steps` (progress pills), `active` (index), `feed` (true = scrolling backlog behind) |
| `cards` | `cards`: [{`title`, `text`, `color`, `cue`}] (up to 8) |
| `checklist` | `items`: [{`text`, `cue`}] (up to 10) |
| `terminal` | `lines`: strings, `$ cmd` is typed, other lines are output (up to 24); `window_title` |
| `browser` | `url`, `heading` (shown inside the page), `nav`, `rows`: [{`text`, `chip`, `color`}], `button` (clicked by a moving pointer), `modal`: {`title`, `text`, `button`, `color`} |
| `ide` | `files`, `editor`: {`file`, `code`: lines}, `panel`: {`title`, `mode`, `messages`, `plan`}, `terminal`: lines |
| `flow` | `nodes`: [{`label`, `sub`, `color`}] (2 to 6), `chips` |
| `stats` | `stats`: [{`value`, `label`, `color`}] (up to 4; numbers count up) |
| `feed` | `title`, `columns`, `items`: [{`text`, `chip`, `color`}], `highlight` (row index) |
| `split` | `left` and `right`: two scenes with any layout except `split` |

Common fields: `heading` (top left; on `browser` it is shown inside the page), `callouts` (pills along the bottom), `badges`: [{`text`, `color`}] (up to 3, top right),
`footer` (closing line), `nameplate`: {`name`, `role`}, `background` (`grid`, `feed`, `none`), `label` (corner label).
`cue` is an optional phrase from the voice-over of that scene at which the item appears.

## Output
`narratives/<slug>/storyboard.json`, `narratives/<slug>/production.json`, `narratives/<slug>/production/output/<name>.mp4` and `.srt`,
`production/build/` (timeline.json, audio.wav), `production/review/*.png`

## Follow-up questions and task completion
Activate `narrative-followup-questions` with step `production` (review feedback, re-render scene N, final storage
location, publishing). Then complete the task as described in `video-narrative-workflow`
(outcome record in `task-outcomes/`).
