---
name: narrative-05-script
description: Step 5 of 9 of the video narrative skill system. Use when writing or revising a timed, scene-by-scene video narrative script (TIMING, VISUAL, VO table) from a fact sheet, intake answers and section map.
---

# Step 5 of 9: Script

Writes `narratives/<slug>/<slug>_script_v1.md` from `{{DNB_HOME}}/templates/script_template.md`.
Read `{{DNB_HOME}}/references/methodology.md` once for the detailed quality bar.

## Inputs
`factsheet.md` (step 3), `structure.md` (step 4), `intake.json` (step 1).
Check with `"{{DNB_PYTHON}}" "{{DNB_HOME}}/tools/skills.py" check <slug> 5`. If something is missing,
offer to run the step that produces it; do not guess.

## Steps

1. **Fill the template** in this order, replacing every `{{placeholder}}`:
   change-log comment (run `date`), title, logline, STATUS line, runtime and format line, legend,
   Source fidelity note, Section map (from `structure.md`), Script table, Follow-up questions by
   section, Appendix, APPROVAL GATE. Leave the `PRODUCTION-PLAN-PENDING` marker in place: step 7 fills it.
2. **Script table rules.**
   - Rows `| m:ss-m:ss | VISUAL | VO |`, contiguous, start 0:00, end at the target runtime.
   - VISUAL has `SCENE:`, and where relevant `DEMO:`, `ON-SCREEN:`, `TRANSITION:`. Use `<br>` between labels.
   - VO is first person, spoken English, short sentences, `[BEAT]` for a pause. Budget words as
     window seconds x 2.2 at 150 wpm, minus 1 s for lead-in and tail.
   - Each scene covers facts by id (for example F3, F7) in the Section map "Source basis" column.
   - Mandatory sections requested by the user each get their own section-map row.
3. **Follow-up questions by section.** At least one row per section-map number: the question a viewer or
   reviewer is likely to ask, why it matters, and a suggested answer from the fact sheet or "needs input".
4. **Revisions.** Never overwrite an approved version. Copy to `_v2.md`, add a change-log line, change
   only the requested scenes, then run step 6 again.
5. Show a short summary (sections, runtime, words) and the file path. Do not start any production work.

## Output
`narratives/<slug>/<slug>_script_v1.md` (later `_v2.md`, `_v3.md`; old versions are kept)

## Compatibility
The script table matches the Demobuilder video pipeline parser (`demo_common.load_scenes`), so an
approved script can be rendered by step 9 unchanged.

## Follow-up questions and next step
Activate `narrative-followup-questions` with step `script`. Next: `narrative-06-validate` (step 6).
