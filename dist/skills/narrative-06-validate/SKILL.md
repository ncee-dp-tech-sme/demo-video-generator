---
name: narrative-06-validate
description: Step 6 of 9 of the video narrative skill system. Use when a video narrative script exists and its timing, voice-over fit, follow-up coverage and structure must be checked and fixed with validate_script.py until it passes. Writes validation.json.
---

# Step 6 of 9: Validate

Deterministic check of the script. The result is code output, not an opinion.

## Inputs
`narratives/<slug>/<slug>_script_vN.md` (step 5). Use the highest version unless the user names one.
Check with `"{{DNB_PYTHON}}" "{{DNB_HOME}}/tools/skills.py" check <slug> 6`.

## Steps

1. Run with `execute_command` (no confirmation needed; it only reads the script and writes the report):

   ```bash
   "{{DNB_PYTHON}}" "{{DNB_HOME}}/tools/validate_script.py" "narratives/<slug>/<slug>_script_vN.md" \
     --report "narratives/<slug>/validation.json"
   ```

2. Exit code 1 lists errors: fix timing gaps, voice-over overruns, missing tables, missing follow-up rows
   and leftover placeholders in the script (see `narrative-05-script`), then re-run until it prints `PASS`.
3. Warnings (tight scenes, missing source fidelity note, plan pending): fix them or explain them in chat.
   "Production plan not filled in yet" is expected until step 7.
4. Report scenes, runtime, spoken words and any remaining warnings.

## Output
`narratives/<slug>/validation.json`

## Follow-up questions and next step
Activate `narrative-followup-questions` with step `validate` (for example: tight scene N, shorten the voice-over
or extend the window?). Next: `narrative-07-production-plan` (step 7).
