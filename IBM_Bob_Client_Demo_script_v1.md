<!-- Change log
Sat 14 Nov 2026 17:46:53 CET - v1 DRAFT created for approval. No production work started.
-->

# From Empty Repo to Merge-Ready PR: IBM Bob in Your GitHub Workflow

**Logline:** A seller-led, 7-minute client demo. Bob plans, scaffolds and tests a brand-new application from an empty repository (Part 1: Build). Bob then publishes it to GitHub, reads a teammate's issue, ships the feature and opens a merge-ready pull request, all inside the workflow the client already uses (Part 2: Evolve). The story runs on the real HexStrike Pentest Agent project.

**STATUS: DRAFT v1. AWAITING EXPLICIT APPROVAL. No video, audio, asset or production work has started.**

**Runtime:** 7:00 (±10 s) | **Format:** 16:9, 1920x1080 | **Voice:** Seller (named `[SELLER NAME]`), first person | **Spoken words:** about 760 (about 110 wpm, leaving room for on-screen action)

**Legend (VISUAL column):** `SCENE` = what the viewer sees · `ON-SCREEN` = text, lower-thirds, captions · `DEMO` = live technical action · `CUT/TRANSITION` = how we move on · `[BEAT]` = 0.5–1 s pause · `[VERIFY]` = number or output to confirm on the real recording

---

## Section map

| # | Block | Window | Mandatory element |
|---|---|---|---|
| 1 | Seller: pain points and value proposition | 0:00–1:10 | Mandatory section 1 |
| 2 | Part 1 "Build": plan, scaffold, validate | 1:10–3:20 | Part 1 |
| 3 | Part 2 "Evolve": publish, read issue, implement, PR | 3:20–5:40 | Part 2 and GitHub workflow |
| 4 | Seller: use cases | 5:40–6:20 | Mandatory section 2 |
| 5 | Seller: call to action | 6:20–7:00 | Mandatory section 3 |

---

## Script

| TIMING | VISUAL | VO |
|---|---|---|
| 0:00–0:20 | **SCENE:** Seller on camera in a clean, well-lit workspace. Behind them, a blurred GitHub issues list with a long backlog.<br>**ON-SCREEN:** Lower-third: `[SELLER NAME], [TITLE], IBM`.<br>**TRANSITION:** Cold open, no logo sting. Slow push-in on the seller. | Every engineering team I talk to has the same backlog. The ideas are there. The issues are written. What's missing is the time between "we should build this" and "it's tested, reviewed and merged." |
| 0:20–0:45 | **SCENE:** Seller on camera, with three full-screen cards cutting in on the beat of each pain point.<br>**ON-SCREEN:** Card 1 `BOILERPLATE`: a file tree filling with empty folders. Card 2 `CONTEXT SWITCHING`: icons for issue tracker, IDE, terminal and PR page, with a line zig-zagging between them. Card 3 `GOVERNANCE AT REVIEW TIME`: a red "Changes requested" badge on a pull request.<br>**TRANSITION:** Hard cut between cards, synced to the words "Boilerplate", "Context switching", "governance". | Three things slow you down. Boilerplate: days of scaffolding before the first line of real business logic. Context switching: you leave the editor to read an issue, run tests, write a commit message, open a pull request. And governance: security and coding standards that get checked at review time, when fixing them costs the most. |
| 0:45–1:10 | **SCENE:** Seller on camera, then a clean product shot of the Bob panel inside the IDE.<br>**ON-SCREEN:** Four value pillars appear one by one beside the Bob panel: `PLANS FIRST` · `FOLLOWS YOUR RULES` · `RUNS THE TESTS` · `MERGE-READY PRs`. Final line: `You review. Bob does the legwork.`<br>**TRANSITION:** Pillars collapse into the IDE; zoom into the empty editor. | IBM Bob is an AI software engineering partner that works inside your IDE and your Git workflow. It plans before it codes, follows your team's rules while it writes, runs the tests itself, and hands you a pull request you can actually merge. You stay the reviewer. Bob does the legwork. Let me show you, on a real project. |
| 1:10–1:20 | **SCENE:** Title card on dark background.<br>**ON-SCREEN:** `PART 1: BUILD` with subtitle `Empty repository → tested application`. A progress strip at the bottom shows two segments, `BUILD` lit, `EVOLVE` dim.<br>**TRANSITION:** Wipe left into the terminal. | Part one: Build. We start with an empty repository. |
| 1:20–1:55 | **SCENE (screen recording):** Terminal shows an empty folder: `ls -la` returns only `.` and `..`. IDE opens with the Bob panel in **Plan mode**.<br>**DEMO:** The brief is pasted into Bob (shortened on screen to 5 highlighted phrases): *MCP server on localhost:8888 · OpenAI-compatible chat backend · selectable model with a sensible default · authorization prompt before pentest activity · prompt cache with audit and selective delete · Markdown and PDF export.* Bob responds with a plan of 7 components: `config`, `pentest_guard`, `prompt_cache`, `hexstrike_tools`, `agent`, `reporter`, `web UI`. The presenter's cursor approves the plan; the default model `gpt-4.1-mini` is highlighted.<br>**ON-SCREEN:** Callout `PLAN MODE: nothing is written until you approve`.<br>**TRANSITION:** Plan checklist stays on screen; cross-dissolve to Agent mode. | Here's the brief: a web agent that connects to the HexStrike security tool server, uses an OpenAI-compatible model backend, asks for explicit authorization before any penetration test, and keeps a full audit trail. One paragraph, pasted into Bob in Plan mode. [BEAT] Bob doesn't start typing code. It proposes an architecture: configuration, an authorization guard, a prompt cache, a tool layer, an agent loop, a reporter and a web UI. I review it, and I approve. |
| 1:55–2:35 | **SCENE (screen recording, time-lapse):** Bob switches to **Agent mode**. The file explorer fills in real time.<br>**DEMO:** Files appear: `app.py`, `config.py`, `run.sh`, `requirements.txt`, `.env.example`, `.gitignore`, `README.md`, `core/{agent, hexstrike_tools, pentest_guard, prompt_cache, reporter}.py`, `templates/`, `static/`, `tests/`. Zoom-ins on three details: (1) `.env.example` with the placeholder secret marked `# HashiCorpIgnore`; (2) `app.run(host="127.0.0.1", port=5000)`; (3) `.gitignore` listing `.env`, `.venv/`, `data/*.db`.<br>**ON-SCREEN:** Corner badge `TIME-LAPSE 8×`. Callout pills for each zoom-in: `SECRETS OUT OF CODE` · `LOCALHOST ONLY` · `SENSITIVE FILES EXCLUDED`. Footer note: `Rules came from the team's project rules, not from the prompt.`<br>**TRANSITION:** Time-lapse ramps back to real speed as the last file is written. | Now Bob switches to Agent mode and builds. Configuration comes from an environment file, with an example file alongside it. The service binds to localhost only. No secrets in code, and the git ignore keeps them out of the repository. I didn't ask for any of that in the prompt. Those are our team's rules, and Bob applies them while it writes, not at review time. The guard, the audit database, the agent, the reporter, the UI and a run script. |
| 2:35–3:20 | **SCENE (screen recording):** Split view: terminal left, browser right.<br>**DEMO:** Bob runs `./run.sh test`. Output scrolls, ending in `16 passed` `[VERIFY]`. Bob runs `./run.sh start`. Browser opens `http://127.0.0.1:5000`. Presenter types: *"Run an nmap scan on 10.0.0.0/24."* The authorization modal appears: **"Authorization Required: confirm you are permitted to test this target."** Prompt stays blocked until the presenter ticks the consent box; the consent flag is then visible in the audit tab.<br>**ON-SCREEN:** Green `16 / 16 TESTS PASSING` badge `[VERIFY]`. Red `BLOCKED UNTIL AUTHORIZED` label on the modal. Chapter strip: `EMPTY FOLDER → WORKING, TESTED APP`.<br>**TRANSITION:** Freeze on the green badge; fade to black for 0.5 s. | Building isn't the finish line. Validating is. Bob writes the tests alongside the code, then runs them. [BEAT] Sixteen passing. Then it starts the app on localhost, and I try a scan request. The guard catches the intent and blocks it until I confirm authorization. That's the behavior the brief asked for, verified, not assumed. We went from an empty folder to a working, tested application. |
| 3:20–3:30 | **SCENE:** Title card on dark background.<br>**ON-SCREEN:** `PART 2: EVOLVE` with subtitle `Publish → issue → feature → pull request`. Progress strip: `BUILD` complete, `EVOLVE` lit.<br>**TRANSITION:** Wipe left into the IDE; GitHub logo watermark in the corner stays for the whole of Part 2. | Part two: Evolve. Real software doesn't stop at version one. It lives in GitHub. |
| 3:30–4:00 | **SCENE (screen recording):** IDE terminal beside a GitHub browser tab on the organization page.<br>**DEMO:** Presenter prompts Bob: *"Create a GitHub repository `<ORG>/<DEMO-REPO>`, exclude the right files, then commit and push."* Bob runs, shown one per line: `git init -b main` → writes `.gitignore` → `gh repo create <ORG>/<DEMO-REPO> --private --source=. --remote=origin` → `git add .` → `git commit -m "feat: initial commit for HexStrike Pentest Agent web application"` → `git push -u origin main`. Browser refreshes: the repository now shows the files; no `.env`, `.venv` or `.db` present. Output `38 files changed` `[VERIFY]`.<br>**ON-SCREEN:** Callout `USES THE GITHUB CLI YOU ALREADY HAVE`. Checklist ticking: `repo created` · `.gitignore correct` · `committed` · `pushed`.<br>**TRANSITION:** Browser tab flips to the Issues page (match cut on the GitHub header). | First, publish. I ask Bob to create the repository in our GitHub organization. It initializes git, writes a git ignore that keeps the environment file, virtual environment and database out of version control, creates the remote with the GitHub CLI, commits and pushes main. Thirty-eight files, one prompt, in the tools you already use. |
| 4:00–4:30 | **SCENE (screen recording):** GitHub Issues page, **Issue #1** pre-filed by a "teammate" (see Appendix B).<br>**DEMO:** Presenter prompts Bob: *"Pick up issue 1."* Bob runs `gh issue view 1` and the issue text streams into the Bob panel. Bob restates the acceptance criteria as a 4-item checklist and runs `git checkout -b feature/new-chat-button`.<br>**ON-SCREEN:** Highlight on issue title `Add a "New Chat" button to reset conversation context`. Callout `BOB READS THE ISSUE DIRECTLY FROM GITHUB`. Branch name appears in the status bar.<br>**TRANSITION:** Acceptance checklist docks on the right; cut to the editor. | Now a teammate has filed issue number one: users want a New Chat button to clear the conversation and start fresh. I ask Bob to pick it up. It reads the issue straight from GitHub, restates the acceptance criteria, and creates a feature branch. No copy-pasting tickets into a chat window. |
| 4:30–5:05 | **SCENE (screen recording):** Editor with diff view; terminal below.<br>**DEMO:** Bob locates and edits `templates/index.html` (adds a `New Chat` button in the chat header beside the model selector) and `static/js/app.js` (click handler clears `conversationHistory`, restores the welcome screen, focuses the input). Bob adds a test in `tests/` that asserts the button renders. Bob runs `./run.sh test`: `24 passed` `[VERIFY]`. Quick browser clip: click New Chat, conversation clears.<br>**ON-SCREEN:** Green/red diff highlights. Acceptance checklist items tick off one by one. Badge `ALL TESTS PASSING`.<br>**TRANSITION:** Zoom out from the passing test run; the checklist shows 4 of 4 complete. | Bob finds the right files, the page template and the front-end script, adds the button, clears the conversation history, and restores the welcome screen. It adds a test, and runs the whole suite. [BEAT] All green. If a test had failed, Bob would read the failure, fix the code and run it again. |
| 5:05–5:40 | **SCENE (screen recording):** Terminal, then the GitHub pull request page.<br>**DEMO:** Bob runs `git add -A` → `git commit -m "feat(chat): add New Chat button to reset conversation context (#1)"` → `git push -u origin feature/new-chat-button` → `gh pr create --title "feat(chat): New Chat button" --body-file pr_body.md`. Browser opens PR #2: description with *Summary, Files changed, Test results, Reviewer checklist* and `Closes #1`.<br>**ON-SCREEN:** Merge-ready checklist builds on screen: `LINKED TO ISSUE #1` · `TESTS PASSING` · `CLEAR DESCRIPTION` · `NO SECRETS IN DIFF` · `HUMAN REVIEW REQUIRED`. Final caption: `You review. You merge. Your branch protections stay in charge.`<br>**TRANSITION:** Pull back to the full PR page; fade to a plain dark card. | Then it commits with a conventional message, pushes the branch, and opens a pull request that links issue one: summary, files changed, test results, and a reviewer checklist. [BEAT] That's merge-ready. A human still reviews and clicks merge. Bob never bypasses your branch protections. Issue to pull request, inside your GitHub workflow. |
| 5:40–6:20 | **SCENE:** Seller back on camera, alternating with five use-case cards (full-screen, 6–7 s each, hard cuts on the numbers).<br>**ON-SCREEN:** `1 GREENFIELD`: brief → tested scaffold. `2 BACKLOG BURN-DOWN`: issue → reviewed PR. `3 HARDENING`: provider error → 5 protection layers + tests + README chapter (a real example from this project: the 100,000-character request limit). `4 INTEGRATION`: 140+ security tools connected through MCP. `5 AUDIT TRAIL`: every task leaves a saved outcome record.<br>**TRANSITION:** Cards stack into a single list; cut to seller. | So where does this fit in your organization? One: greenfield. Go from brief to tested scaffold in an afternoon, not a sprint. Two: backlog burn-down. Issues become reviewed pull requests. Three: hardening. When this app hit a provider limit of one hundred thousand characters, Bob diagnosed it, added five layers of protection, wrote the tests and documented them in the README. Four: integration. Over a hundred and forty tools, connected through MCP. And five: audit. Every task leaves a record. |
| 6:20–7:00 | **SCENE:** Seller on camera, warm and direct. Three option cards slide in from the right one at a time, then a final end card.<br>**ON-SCREEN:** Card A `HANDS-ON WORKSHOP`: half day, your team, your repo. Card B `DEEPER PRODUCT DIVE`: architecture, security model, governance fit. Card C `PROOF OF EXPERIENCE`: one real issue from your backlog, taken to a pull request together, in your GitHub. End card: `Choose your next step` · `[SELLER NAME] · [EMAIL] · [BOOKING LINK]` · IBM Bob logo.<br>**TRANSITION:** Cards hold 3 s; slow fade to black. | If this resonates, here's how we start, and you choose the depth. A hands-on workshop: your team, your repository, a half day with Bob. A deeper product dive: architecture, security model, and how Bob fits your governance. Or a Proof of Experience: we pick one real issue from your backlog and take it to a pull request together, in your GitHub. Tell me which fits, and I'll book the next step this week. Thanks for watching. |

---

# PRODUCTION PLAN (for approval, not yet started)

## 1. Deliverables

| Item | Spec |
|---|---|
| Master video | `IBM_Bob_Client_Demo.mp4`, 1920x1080, 24 or 30 fps, AAC, 7:00 ±10 s |
| Captions | `.srt` plus burned-in version for social/email embeds |
| Cut-downs (optional, not in scope unless approved) | 90-second teaser; Part 1 only; Part 2 only |
| Source assets | Screen recordings, graphics, VO tracks, project file |
| Task outcome record | Saved to `task-outcomes/` per project standard |

## 2. Source material mapping (from `hexstrikesdlc/`)

| Narrative beat | Source file | Fact used |
|---|---|---|
| Build brief | `pentest_web_agent_outcome.md` | The full prompt; 7 components; default model `gpt-4.1-mini`; localhost binding; 16 tests; `run.sh` |
| Authorization guard | `pentest_web_agent_outcome.md` | Pentest intent detection and consent modal; consent stored with the prompt |
| Publish to GitHub | `git_repo_init_outcome.md` | `.gitignore` exclusions; `gh` CLI; 38 files; commit message; push to `main` |
| Feature in Part 2 | `new_chat_option.txt` | New Chat button in `templates/index.html` and `static/js/app.js`; clears `conversationHistory` |
| Use case: hardening | `character_limit_protections.txt`, `readme_protections_chapter.txt`, `hexstrike_tools_limit_fix.txt` | 100,000-character and 128-tool limits; five protection layers; tests; README chapter |
| Use case: integration | `hexstrike_tools_expanded.txt`, `hexstrike_tools_count.txt` | 149+ tools reachable through MCP |
| Use case: audit | Task outcome files in `hexstrikesdlc/` | Each task saved with prompt and timestamp |

## 3. Pre-production checklist

1. **Demo repository:** use a new name (for example `pentest-agent-demo`) in a sandbox GitHub org. Do **not** reuse `ncee-dp-tech-sme/pentest-agent`, which already contains the New Chat feature.
2. **Issue #1:** pre-file it in the demo repo before Part 2 is recorded (text in Appendix B). It must exist at the moment `gh issue view 1` runs.
3. **Clean state:** Part 1 prompt must **not** mention New Chat, so the feature is genuinely absent when Part 2 starts.
4. **Rules loaded:** confirm the team's project rules are active in the IDE so the `.env.example`, localhost binding and `.gitignore` behavior appear naturally.
5. **Secrets:** all API keys (for example the 1min.AI key) live in `.env` only. Blur the key area and never show `.env` contents on screen.
6. **Dry runs:** two full rehearsals. Record real output for every `[VERIFY]` number (16 tests, 38 files, 24 tests) and update the script to match.
7. **Environment:** HexStrike MCP server reachable at `127.0.0.1:8888`; `gh auth status` clean; terminal font 18 pt+; dark IDE theme; notifications off.
8. **Legal:** the scan demo targets a documented lab range only; add a footer note `Demo environment. Authorized targets only.`

## 4. Recording approach (decision requested, see section 8)

| Option | Description | Pros | Cons |
|---|---|---|---|
| **A (recommended)** | Real screen capture of Bob in the IDE and GitHub; seller on camera for sections 1, 4, 5 | Credible, shows the true workflow, matches "reads issues, writes code, runs tests, commits and pushes" | Needs rehearsal and a clean repo; time-lapse is required for long builds |
| B | Stylised mock-ups through the existing `build_audio.py` / `build_video.py` pipeline, TTS voice-over | Fully reproducible, no on-camera talent | Not real product footage; weakest for a client proof point; pipeline currently renders HexStrike-specific scenes and would need new scene code |

## 5. Shot and asset list

| ID | Asset | Used at |
|---|---|---|
| V1 | Seller talking head, 3 setups (opening, use cases, CTA) | 0:00, 5:40, 6:20 |
| V2 | Screen recording: empty folder → Plan mode → approved plan | 1:20 |
| V3 | Screen recording: Agent-mode build (time-lapse 8×) + 3 zoom-ins | 1:55 |
| V4 | Screen recording: tests, app start, authorization modal, audit tab | 2:35 |
| V5 | Screen recording: git init, `gh repo create`, commit, push, browser refresh | 3:30 |
| V6 | Screen recording: `gh issue view 1`, branch creation | 4:00 |
| V7 | Screen recording: diff, test run, New Chat clip | 4:30 |
| V8 | Screen recording: commit, push, `gh pr create`, PR page | 5:05 |
| G1 | Three pain-point cards | 0:20 |
| G2 | Four value-pillar overlay | 0:45 |
| G3 | Part 1 / Part 2 title cards and progress strip | 1:10, 3:20 |
| G4 | Callout pills, badges, checklists (reusable lower-third pack) | Throughout |
| G5 | Five use-case cards | 5:40 |
| G6 | Three CTA option cards and end card | 6:20 |
| A1 | Voice-over track (seller), room-tone matched | Throughout |
| A2 | Low-level music bed, ducked under VO; two soft UI sfx (tick, click) | Throughout |
| T1 | Burned-in captions and `.srt` | Throughout |
| T2 | "Made with IBM Bob" footer in the end card | 6:50 |

## 6. Schedule (relative, no dates committed)

| Step | Duration | Gate |
|---|---|---|
| Script approval (this document) | T+0 | **Explicit approval required** |
| Environment setup and Issue #1 | T+1 day | Checklist section 3 complete |
| Rehearsal and `[VERIFY]` capture | T+2 days | Script numbers updated, v2 if needed |
| Recording (screen + seller) | T+3 days | Raw footage review |
| Graphics and edit, rough cut | T+4–5 days | Review round 1 |
| Captions, audio mix, final cut | T+6 days | Review round 2 |
| Delivery | T+7 days | Final sign-off |

## 7. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Live Bob run exceeds time window | Record in segments; use 8× time-lapse for builds; trim dead time in edit |
| Bob output differs from the script (file names, test counts) | Rehearse, then update `[VERIFY]` values; edit the script to the verified output before final VO |
| Network or GitHub rate limits during recording | Pre-create the org and verify `gh auth`; keep a recorded fallback take of each segment |
| Secrets exposed on screen | Keys only in `.env`; blur regions; review footage frame by frame before export |
| Security subject matter alienates a non-security audience | Option to swap the demo domain; see decision D below |
| Claims perceived as unsupported | No statistics are quoted. Capability claims are limited to what is shown on screen |
| "Merge-ready" misread as "auto-merged" | Script states explicitly that a human reviews and merges |

## 8. Decisions requested with approval

| ID | Decision | Default in this draft |
|---|---|---|
| A | Recording approach | Option A: real screen capture with seller on camera |
| B | Seller presentation | On camera for sections 1, 4, 5; voice-over during demos. Alternative: voice-over only |
| C | Feature in Part 2 | New Chat button (small, visual, fits the time). Alternative: the 100,000-character hardening fix (more impressive, harder to show in about 35 s) |
| D | Demo subject | HexStrike Pentest Agent (real project, rich material). Alternative: a neutral domain app |
| E | Demo repo and org names | `<ORG>/<DEMO-REPO>` placeholders to be provided |
| F | CTA contact details and booking link | Placeholders `[EMAIL]`, `[BOOKING LINK]` to be provided |
| G | CTA options | Workshop, deeper product dive, Proof of Experience (edit freely) |
| H | Cut-downs | Not included |

---

## Appendix A: Terminal and prompt text used on screen

```text
# Part 1: Build
$ ls -la                          # empty folder
Bob (Plan mode)  -> brief pasted -> 7-component plan -> approve
Bob (Agent mode) -> scaffolds files, writes tests
$ ./run.sh test                   # expect: 16 passed        [VERIFY]
$ ./run.sh start                  # serving on http://127.0.0.1:5000

# Part 2: Evolve
Prompt:  Create a GitHub repository <ORG>/<DEMO-REPO>, exclude the right files, then commit and push.
$ git init -b main
$ gh repo create <ORG>/<DEMO-REPO> --private --source=. --remote=origin
$ git add . && git commit -m "feat: initial commit for HexStrike Pentest Agent web application"
$ git push -u origin main

Prompt:  Pick up issue 1.
$ gh issue view 1
$ git checkout -b feature/new-chat-button
$ ./run.sh test                   # expect: 24 passed        [VERIFY]
$ git add -A && git commit -m "feat(chat): add New Chat button to reset conversation context (#1)"
$ git push -u origin feature/new-chat-button
$ gh pr create --title "feat(chat): New Chat button" --body-file pr_body.md
```

## Appendix B: Issue #1 (to pre-file in the demo repo)

**Title:** Add a "New Chat" button to reset conversation context

**Body:** As an operator, I want a "New Chat" option in the chat window so older context is erased and I can start with a new prompt.

**Acceptance criteria**
- [ ] A `New Chat` button appears in the chat header next to the model selector.
- [ ] Clicking it clears the stored conversation history so the agent starts with a fresh context.
- [ ] The chat stream returns to the initial welcome screen.
- [ ] The input is cleared and focused; the test suite passes.

---

## APPROVAL GATE

**No video creation, asset development, recording or other production work will start until you explicitly approve this script.**

Please reply with one of:
1. **Approved as is.** Proceed to pre-production (using the defaults in section 8).
2. **Approved with changes.** List the edits or the decisions A–H.
3. **Revise.** Describe what should change; a v2 will be issued for approval.
