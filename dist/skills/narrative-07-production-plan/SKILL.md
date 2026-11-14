---
name: narrative-07-production-plan
description: Step 7 of 9 of the video narrative skill system. Use when a validated video narrative script needs its production plan (deliverables, source mapping, approach, assets, work plan, risks, decisions) written before it is presented for approval.
---

# Step 7 of 9: Production plan

Replaces the `PRODUCTION-PLAN-PENDING` marker in the script with the filled plan. This is planning only: no
audio, video or asset work starts here.

## Inputs
A script that passed step 6 and `validation.json`.
Check with `"{{DNB_PYTHON}}" "{{DNB_HOME}}/tools/skills.py" check <slug> 7`.

## Steps

1. Read the script, `factsheet.md` and `intake.json`.
2. Fill `{{DNB_HOME}}/templates/production_plan_template.md` (sections 1 to 7):
   Deliverables, Source material mapping (beat to source section to fact id), Approach (visual approach,
   voice, pace in wpm, pronunciation fixes), Asset list, Work plan after approval, Risks, Decisions.
3. The work plan matches step 9: gate check, audio, review frames, render, record.
   Name the production engine: the generic storyboard renderer (default) or a story-specific renderer.
   Be honest in Approach: the generic renderer produces text cards, not product footage.
4. Replace the marker line in the script with the filled plan (keep the `# PRODUCTION PLAN` heading).
   List every placeholder the user still has to supply under Decisions.
5. Re-validate with the plan required:

   ```bash
   "{{DNB_PYTHON}}" "{{DNB_HOME}}/tools/validate_script.py" "<script path>" --require-plan \
     --report "narratives/<slug>/validation.json"
   ```

   Fix errors until `PASS`.

## Output
The updated script file (plan section filled in) and a refreshed `validation.json`.

## Follow-up questions and next step
Activate `narrative-followup-questions` with step `plan` (visual approach, voice, reviewer, brand assets).
Next: `narrative-08-approval-gate` (step 8).
