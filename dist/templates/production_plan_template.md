<!-- Body of the production plan. Step 7 replaces the PRODUCTION-PLAN-PENDING marker in the script with this content. -->

## 1. Deliverables

| Item | Spec |
|---|---|
| Master video | `{{slug}}.mp4`, 1920x1080, 24 fps, AAC, {{M:SS}} ±10 s |
| Captions | `.srt` plus burned-in captions |
| Source assets | VO tracks, timeline.json and build folder under `narratives/{{slug}}/production/` |
| Task outcome record | `task-outcomes/{{slug}}.txt` |

## 2. Source material mapping

| Narrative beat | Source section | Fact used |
|---|---|---|
| {{beat}} | {{source heading or page}} | {{F-id and the fact}} |

## 3. Approach

{{Selected recording approach, voice, pacing (words per minute), pronunciation fixes for product names.}}

## 4. Asset list

| ID | Asset | Used at |
|---|---|---|
| {{G0}} | {{asset}} | {{time}} |

## 5. Work plan, after approval

| Step | Output | Check |
|---|---|---|
| 1. Gate check | `approval.json` matches this script version | `production.py check` passes |
| 2. Audio | VO per scene, `timeline.json`, `audio.wav` | No scene overran its window |
| 3. Review frames | `still` and `sheet` PNGs | User confirms the look |
| 4. Render | `{{slug}}.mp4` and `.srt` | Runtime within tolerance |
| 5. Record | `production.json`, `task-outcomes/{{slug}}.txt` | Files listed with sha256 |

## 6. Risks and mitigations

| Risk | Mitigation |
|---|---|
| {{risk}} | {{mitigation}} |

## 7. Decisions

| ID | Decision | Status |
|---|---|---|
| A | {{decision}} | {{default or chosen by user}} |
