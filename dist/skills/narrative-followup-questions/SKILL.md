---
name: narrative-followup-questions
description: Use at the end of each of the nine steps of the video narrative skill system (intake, ingest, facts, structure, script, validate, plan, approval, production) to generate and record 3-5 specific potential follow-up questions with suggested defaults.
---

# Narrative follow-up questions

Produces the questions that keep the user in control at every step.

## Steps

1. Identify the step: `intake`, `ingest`, `facts`, `structure`, `script`, `validate`, `plan`, `approval`, `production`
   (steps 1 to 9; the mapping is in `{{DNB_HOME}}/registry.json`).
2. Read `{{DNB_HOME}}/references/followup-question-bank.md` for that step's prompts and the quality bar.
3. Write 3 to 5 questions that are specific to this source and this step:
   - Each names a concrete thing (a fact id, a section number, a scene time, a term from the source).
   - Each has a suggested default so the user can reply "defaults".
   - Skip anything already answered in `narratives/<slug>/followups.md`.
   - Put the most decision-relevant question first.
4. Show them as a numbered list in chat:

   ```text
   Potential follow-up questions (step: facts)
   1. <question>  [default: <answer>]
   2. ...
   ```

5. Append the same block to `narratives/<slug>/followups.md` under a `## Step: <name>` heading,
   with the date from `date`. When the user answers, add `Answer: ...` under each question.
6. If the user wants one question at a time, use `ask_followup_question` with 2 to 4 suggested answers.

## Do not
Ask more than 5 questions per step, ask about things the source already states, or hide a blocking
question among optional ones (mark blockers with `[blocking]`).
