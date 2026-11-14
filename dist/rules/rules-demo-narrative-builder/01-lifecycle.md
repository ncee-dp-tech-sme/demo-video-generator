# Task lifecycle (mandatory for the Demo Narrative Builder mode)

These rules restate the lifecycle from the team's global coding standards for this mode. If the global
standards are also installed, both apply; the stricter rule wins.

## Phase 1: Pre-flight
- Python tools run only with the asset's virtual environment: `{{DNB_PYTHON}}`. Never use the system
  Python and never install packages globally. If that interpreter is missing, tell the user to re-run
  `install.py`; do not improvise a different environment.
- Before running any script that writes files or touches the network (ingest of a URL, installers,
  step 9 production), show a short summary of what will happen, name any risk (network access,
  overwriting an existing folder in `narratives/`, overwriting `production/` output, CPU-heavy rendering)
  and ask for confirmation. Reading local files and running `validate_script.py`, `skills.py`
  and `approval.py verify` need no confirmation.

## Phase 2: Scoping
- Use `update_todo_list` for the nine workflow steps (the nine step skills, step 9 being video production). Mark a step in progress only in the same update
  that completes the previous one.
- Large documents: if the final script or plan becomes long, write it in separate chapter files
  and merge them in order into one file.

## Phase 3: Implementation standards
- Run `date` (no options) to get timestamps. Never invent a date.
- Every generated script starts with an HTML change log comment: one line per change, chronological,
  `<timestamp> - <short description>`.
- User-provided runtime values (target runtime, speaking pace, output folder, language) come from
  the intake answers or `{{DNB_HOME}}/.env`, never from hard-coded values.
- Keep changes surgical: when the user asks for edits to an approved script, issue a new version
  (`_v2.md`), keep the old one, and add a change-log line. Do not rewrite untouched scenes.

## Phase 4: Task completion (persist to disk)
- When a task ends, write the results shown in chat to `task-outcomes/<task-name>.txt`
  (create the folder if needed). One file per task; sub-steps are combined into that file.
- The file starts with the exact user prompt, then the timestamp from `date`, then the outcome:
  files created, validation result, open questions, approval status.
- Keep the file compact. Do not paste whole scripts into it; list their paths.
