# Narrative methodology (the same method as the IBM Bob client demo and HexStrike scripts)

## Order of work
1. Intake: audience, goal, runtime, presenter, mandatory sections, call to action.
2. Ingest the source with the tool (URL, PDF, TXT, DOCX).
3. Fact sheet: key facts, each with its source section.
4. Structure: a section map with time windows.
5. Script: the three-column table `| TIMING | VISUAL | VO |`.
6. Validate with `validate_script.py` and fix every error.
7. Production plan: deliverables, source mapping, approach, assets, work plan, risks, decisions.
8. Approval gate: stop and ask for explicit approval; record it with `approval.py`.
9. Video production: audio, review frames and MP4 with captions from the approved script (`production.py`).

Each step is its own skill (`narrative-01-intake` to `narrative-09-video-production`, listed in `registry.json`)
and can be run on its own when its inputs exist (`skills.py check <slug> <step>`). Step 9 is a full step like the
others: it gets its own follow-up questions and its own output file (`production.json`). After step 9, or
whenever a task stops earlier, write the outcome record in `task-outcomes/`.

## Follow-up questions at every step
- End each step with 3 to 5 numbered potential follow-up questions, each with a suggested default
  answer, so the user can answer with "defaults" or pick numbers.
- Record them in `narratives/<slug>/followups.md` under the step heading, with the answer once given.
- Questions must be specific to the source and the step. Do not repeat answered questions.

## Script rules
- Table rows follow `| m:ss-m:ss | VISUAL | VO |`, are contiguous, start at 0:00 and end at the target runtime.
- VISUAL uses the legend labels `SCENE`, `ON-SCREEN`, `DEMO`, `TRANSITION`; `[BEAT]` marks a 0.5 to 1 s pause.
- VO is first person, plain spoken English, about the configured words per minute, and fits its window.
- Every fact in VO or on-screen text traces to the fact sheet. Anything the source does not state is
  either left out or marked as illustrative in the Source fidelity note.
- Include: STATUS line, Runtime line, Legend, Source fidelity note, Section map, script table,
  Follow-up questions by section, Production plan, Decisions, Appendix, APPROVAL GATE.
- The mandatory sections requested by the user (for example pain points, use cases, call to action)
  are never dropped or merged.

## Approval gate
- Never start audio, video, assets or other production work until the user replies with explicit
  approval (option 1 or 2 of the gate). On "approved with changes", issue a new version first.
- The gate offers exactly: 1 Approved, 2 Approved with changes, 3 Revise.
- Step 9 starts only if `approval.py verify` succeeds for the exact script file; editing the script afterwards
  invalidates the approval. Never bypass `production.py` by calling `say`, ffmpeg or the build scripts directly.
- Visuals made by the generic renderer are placeholders; say so when reporting the result.
