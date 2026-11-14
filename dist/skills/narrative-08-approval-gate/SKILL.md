---
name: narrative-08-approval-gate
description: Step 8 of 9 of the video narrative skill system. Use when a validated script with a filled production plan must be presented to the user for explicit approval (Approved, Approved with changes, Revise) and the decision recorded before any production starts.
---

# Step 8 of 9: Approval gate

Nothing is produced until the user explicitly approves this exact script version. The approval is recorded by
code and bound to the file's sha256, so step 9 can verify it.

## Inputs
The latest script with its production plan filled (step 7).
Check with `"{{DNB_PYTHON}}" "{{DNB_HOME}}/tools/skills.py" check <slug> 8`.

## Steps

1. Present a short summary (sections, runtime, words, validation PASS, open placeholders, production engine)
   and the three options. Use `ask_followup_question` with these suggested answers:
   1. Approved. 2. Approved with changes (user lists the edits). 3. Revise (user describes what to change).
2. **Option 1:** record it.

   ```bash
   "{{DNB_PYTHON}}" "{{DNB_HOME}}/tools/approval.py" record "<script path>" --option 1
   ```

   The tool re-validates with the plan required, sets the STATUS line to APPROVED, adds a change-log line and
   writes `narratives/<slug>/approval.json`.
3. **Option 2:** apply only the listed edits as a new version (`_v2.md`, keep `_v1.md`, change-log line),
   re-validate (step 6 commands with `--require-plan`), show what changed, then record with
   `--option 2 --note "<short summary of the changes>"` on the new version.
4. **Option 3:** write the new version, re-validate, and ask again from step 1 of this skill.
5. Never record an approval that the user did not give in this conversation. Silence, "looks good so far"
   or an answer to a different question is not approval.
6. After any edit to an approved script, the approval no longer matches; run this step again.

## Output
`narratives/<slug>/approval.json` (and the script with an APPROVED status line)

## Follow-up questions and next step
Activate `narrative-followup-questions` with step `approval` (open placeholders, where to store final assets).
Next, only after approval: `narrative-09-video-production` (step 9). If the user does not want a video yet,
go to task completion in `video-narrative-workflow` and record approval status in the outcome file.
