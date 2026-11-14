---
name: narrative-01-intake
description: Step 1 of 9 of the video narrative skill system. Use when starting a video narrative or demo script, or when the audience, goal, runtime, presenter, mandatory sections or call to action are unknown or must be changed. Writes intake.json.
---

# Step 1 of 9: Intake

Collects everything later steps need so they never have to guess. Can be run on its own at any time to
change the answers.

## Inputs
None. Optional: the user's first prompt (source, runtime, audience).

## Steps

1. Run `date` for the timestamp. Pick a slug from the title or source name (lowercase letters, digits,
   dashes) and confirm it.
2. Use `ask_followup_question` (one question per turn, with suggested answers) only for what is still
   missing:
   - source: `https://` URL or a path to `.pdf`, `.txt`, `.md`, `.docx`
   - audience (role, prior knowledge) and goal (what the viewer should do afterwards)
   - target runtime (default 3:00) and speaking pace (default 150 wpm)
   - presenter name and role, or voice-over only (default voice-over)
   - mandatory sections (for example pain points, value proposition, use cases, call to action)
   - call-to-action options and contact details that may be shown (never invent them; use placeholders)
   - tone and output language (defaults: confident and plain, English)
3. Write `narratives/<slug>/intake.json` (create the folder if needed):

   ```json
   {
     "slug": "my-post", "title": "Working title", "created": "<date output>",
     "source": "https://example.com/blog/my-post",
     "audience": "...", "goal": "...", "runtime": "3:00", "wpm": 150,
     "presenter": "voice-over", "mandatory_sections": ["pain points", "use cases", "call to action"],
     "cta_options": ["workshop"], "tone": "...", "language": "en"
   }
   ```

4. Show the answers as a short table and the file path.

## Output
`narratives/<slug>/intake.json`

## Follow-up questions and next step
Activate `narrative-followup-questions` with step `intake`. Next: `narrative-02-ingest` (step 2).
