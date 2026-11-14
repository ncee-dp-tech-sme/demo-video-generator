---
name: narrative-04-structure
description: Step 4 of 9 of the video narrative skill system. Use when a fact sheet and intake answers exist and the section map (blocks, time windows, source basis) of the video must be proposed, adjusted and recorded in structure.md.
---

# Step 4 of 9: Structure

Decides what the video says, in which order and for how long, before any script text is written.

## Inputs
`factsheet.md` (step 3) and `intake.json` (step 1).
Check with `"{{DNB_PYTHON}}" "{{DNB_HOME}}/tools/skills.py" check <slug> 4`.

## Steps

1. Read `intake.json` (runtime, mandatory sections) and `factsheet.md` (ranked facts, demo moments).
2. Propose a section map as a table with these columns: `#`, `Block`, `Window`, `Source basis`.
   - Windows are contiguous, start at 0:00 and end at the target runtime.
   - Every mandatory section from the intake gets its own row; none are merged or dropped.
   - Proven client order: pain, value, proof or demo, use cases, call to action. Open with the
     outcome or the problem, never with a logo.
   - "Source basis" lists fact ids (for example F3, F7); blocks without a fact are marked "illustrative".
3. Write it to `narratives/<slug>/structure.md` with a one-line rationale per block and the list of
   facts left out.
4. Show the table in chat and adjust after the user's answers (rewrite the file, do not append).

## Output
`narratives/<slug>/structure.md`

## Follow-up questions and next step
Activate `narrative-followup-questions` with step `structure`. Next: `narrative-05-script` (step 5).
