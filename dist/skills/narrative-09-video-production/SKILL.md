---
name: narrative-09-video-production
description: Step 9 of 9 of the video narrative skill system. Use when the user wants the video made from an approved narrative script - voice-over, review frames, rendered MP4 and captions - or asks to run, redo or check "step 9" or video production.
---

# Step 9 of 9: Video production

Produces the audio, the review frames and the MP4 with captions from an approved script. It is a full skill
like the other eight: it can be started on its own for any narrative folder that has an approved script.

## Inputs
`narratives/<slug>/<slug>_script_vN.md` and `approval.json` (step 8) for exactly that file.
Check with `"{{DNB_PYTHON}}" "{{DNB_HOME}}/tools/skills.py" check <slug> 9`. If it is not ready, say what is
missing and offer step 8 (or earlier steps); never produce from an unapproved or edited script.

## Steps

1. **Gate and prerequisites.** Run:

   ```bash
   "{{DNB_PYTHON}}" "{{DNB_HOME}}/tools/production.py" check "<script path>"
   ```

   It verifies the approval hash, validates the script and checks `DEMOBUILDER_DIR` (in `{{DNB_HOME}}/.env`), macOS `say`,
   the font and the pipeline Python (pillow, numpy, imageio-ffmpeg). Each problem is listed; relay it and stop.
   Do not work around the gate with other tools.
2. **Pre-run summary and risk warning, then confirmation.** Say what will happen: the voice-over is
   synthesised with macOS `say` (voice from `VOICE`), frames are rendered with Pillow using several CPU cores
   (minutes of runtime for a long video), files are written under `narratives/<slug>/production/`, and an
   existing `production/` output for the same script is overwritten. Ask with `ask_followup_question`
   (Proceed / Audio and review frames only / Cancel). `say` and ffmpeg may need the sandbox to be relaxed;
   ask the user to approve that, do not change sandbox settings yourself.
3. **Audio.** After confirmation:

   ```bash
   "{{DNB_PYTHON}}" "{{DNB_HOME}}/tools/production.py" run "<script path>" --stage audio --confirmed
   ```

   Report the runtime and any `scenes_extended` (voice-over that overran its window and borrowed time).
4. **Review frames.** `--stage sheet --confirmed` writes one PNG per scene to `production/review/`; `--stage still --at <sec> --confirmed`
   writes one frame. Show a few with `read_file` and ask the user to confirm the look before rendering.
5. **Render.** `--stage video --confirmed` renders the frames, muxes the audio and writes `<name>.mp4` and
   `<name>.srt` to `production/output/`. (`--stage all` runs audio and video in one go.)
6. **Engines.** Default is the generic storyboard renderer (text cards from the VISUAL column plus burned-in
   captions). For story-specific scenes (for example the IBM Bob client demo) pass
   `--custom-audio build_<x>_audio.py --custom-video build_<x>_video.py`; both files must already exist in `DEMOBUILDER_DIR`.
   This skill does not write renderer code.
7. **Record.** `production.json` lists stages, outputs with size and sha256, runtime and extended scenes.
   Report the file paths, runtime against target and any warnings. Mark the visuals honestly: generic cards are
   placeholders, rendered mock-ups are illustrations (see the Source fidelity note in the script).

## Output
`narratives/<slug>/production.json`, `narratives/<slug>/production/output/<name>.mp4` and `.srt`,
`production/build/` (timeline.json, audio.wav), `production/review/*.png`

## Follow-up questions and task completion
Activate `narrative-followup-questions` with step `production` (review feedback, re-render scene N, final storage
location, publishing). Then complete the task as described in `video-narrative-workflow`
(outcome record in `task-outcomes/`).
