# Scenes 7-13 of the IBM Bob client demo (Part 2: Evolve, use cases, call to action).
#
# Change log
# Sat 14 Nov 2026 18:20 CET - Initial version.

from PIL import Image, ImageDraw

import demo_common as C
from bob_scenes_a import backlog_layer
from bob_ui import (AMBER, BG, CODE_BG, CYAN, GH_BG, GH_LINE, GREEN, H, IBM, IBM_DARK, K, LINE, MUTED, PANEL,
                    PANEL2, PURPLE, RED, T, TXT, W, WHITE, blink, bob_panel, box, callout, check, chip, clamp,
                    code, font, gh_page, mix, nameplate, paint_backdrop, prog, term, title_card, typed, win,
                    wrap, zoomed)
from build_video import chrome

REPO = "<ORG>/<DEMO-REPO>"
ISSUE_TITLE = 'Add a "New Chat" button to reset conversation context'
CRITERIA = ["New Chat button in the chat header, next to the model selector",
            "Clicking it clears the stored conversation history",
            "Chat returns to the initial welcome screen",
            "Input is cleared and focused; test suite passes"]


# Scene 7: Part 2 title - Sat 14 Nov 2026 18:20 CET
def s7(img, d, t):
    title_card(img, d, t, 2, "EVOLVE", "Publish  →  issue  →  feature  →  pull request", 1)


# Scene 8: publish to GitHub - Sat 14 Nov 2026 18:20 CET
def s8(img, d, t):
    c = K(8)
    paint_backdrop(img)
    t_init, t_ign, t_remote = c("initializes git"), c("writes a git ignore"), c("creates the remote")
    t_commit, t_push, t_38 = c("commits and"), c("pushes main"), c("Thirty-eight files")
    # prompt strip
    cx0, cy0, cx1, cy1 = bob_panel(d, (60, 70, 1100, 250), "AGENT")
    pt = typed(f'Create a GitHub repository {REPO}, exclude the right files, then commit and push.', t - 0.5, 40)
    for j, ln in enumerate(wrap(pt, font(24), 960)):
        T(d, (cx0 + 20, cy0 + 22 + j * 34), ln, font(24), TXT)
    lines = [("$ git init -b main", TXT, t_init), ("Initialized empty Git repository in ./.git/", MUTED, t_init + 1.0),
             ("# writing .gitignore: .env  .venv/  data/*.db  reports/*.pdf  logs/*.log", AMBER, t_ign),
             (f"$ gh repo create {REPO} --private --source=. --remote=origin", TXT, t_remote),
             (f"✓ Created repository {REPO} on GitHub", GREEN, t_remote + 1.8),
             ("$ git add .", TXT, t_commit),
             ('$ git commit -m "feat: initial commit for HexStrike Pentest Agent web application"', TXT, t_commit + 0.8),
             ("[main (root-commit) 3f2a9c1] 38 files changed, 10953 insertions(+)", MUTED, t_commit + 3.2),
             ("$ git push -u origin main", TXT, t_push), ("Branch 'main' set up to track 'origin/main'.", GREEN, t_push + 1.2)]
    term(d, (60, 270, 1100, 800), lines, t, "terminal: pentest-agent", 18, 28)
    # checklist
    steps = [("repo created", t_remote + 1.8), (".gitignore correct", t_ign + 0.5), ("committed", t_commit + 3.2),
             ("pushed", t_push + 1.2)]
    for k, (s, ts) in enumerate(steps):
        check(d, 80 + (k % 2) * 520, 830 + (k // 2) * 50, s, done=t >= ts, f=font(24))
    # GitHub page
    if t < t_remote + 1.8:
        gh_page(d, (1130, 70, 1860, 930), "github.com/<ORG>", None)
        T(d, (1160, 150), "<ORG>", font(40, True), TXT, "lm")
        T(d, (1160, 200), "Repositories", font(22), MUTED, "lm")
        for k, nm in enumerate(["platform-docs", "infra-modules"]):
            d.line((1130, 240 + k * 90, 1860, 240 + k * 90), fill=GH_LINE)
            T(d, (1160, 280 + k * 90), nm, font(26, True), (88, 166, 255), "lm")
    else:
        cx0, cy0, cx1, cy1 = gh_page(d, (1130, 70, 1860, 930), f"github.com/{REPO}", REPO, "Code")
        if t < t_push + 1.2:
            T(d, (cx0 + 30, cy0 + 40), "Quick setup", font(30, True), TXT, "lm")
            T(d, (cx0 + 30, cy0 + 90), "This repository is empty.", font(22), MUTED, "lm")
        else:
            rows = [("core/", "feat: initial commit"), ("static/", "feat: initial commit"), ("templates/", "feat: initial commit"),
                    ("tests/", "feat: initial commit"), (".env.example", "feat: initial commit"), (".gitignore", "feat: initial commit"),
                    ("README.md", "feat: initial commit"), ("app.py", "feat: initial commit"), ("config.py", "feat: initial commit"),
                    ("requirements.txt", "feat: initial commit"), ("run.sh", "feat: initial commit")]
            for k, (nm, msg) in enumerate(rows):
                y = cy0 + 20 + k * 44
                d.line((cx0, y + 40, cx1, y + 40), fill=GH_LINE)
                T(d, (cx0 + 20, y + 18), nm, font(20, mono=True), TXT, "lm")
                T(d, (cx0 + 280, y + 18), msg, font(17), MUTED, "lm")
            if t >= t_38:
                chip(d, cx0 + 20, cy1 - 150, "38 files changed", GREEN, font(22, True), h=44)
            box(d, (cx0 + 14, cy1 - 90, cx1 - 14, cy1 - 20), fill=mix(BG, GREEN, 0.1), outline=GREEN, w=2, rad=10)
            T(d, (cx0 + 34, cy1 - 66), "Not in the repository:", font(18, True), GREEN, "lm")
            T(d, (cx0 + 34, cy1 - 40), ".env   .venv/   data/*.db   reports/*.pdf", font(17, mono=True), TXT, "lm")
    if t >= c("GitHub CLI", -0.3):
        chip(d, 400, 22, "USES THE GITHUB CLI YOU ALREADY HAVE", IBM, font(18, True), h=36)


# Scene 9: read the issue - Sat 14 Nov 2026 18:20 CET
def s9(img, d, t):
    c = K(9)
    paint_backdrop(img)
    t_issue, t_ask, t_view = c("issue number one"), c("I ask Bob"), c("reads the issue straight")
    t_crit, t_branch = c("restates the acceptance criteria"), c("creates a feature branch")
    cx0, cy0, cx1, cy1 = gh_page(d, (60, 70, 1000, 930), f"github.com/{REPO}/issues" + ("/1" if t >= t_issue else ""),
                                 REPO, "Issues")
    if t < t_issue:
        d.line((cx0, cy0 + 8, cx1, cy0 + 8), fill=GH_LINE)
        ellipse_y = cy0 + 50
        d.ellipse((cx0 + 24, ellipse_y - 12, cx0 + 48, ellipse_y + 12), outline=GREEN, width=3)
        T(d, (cx0 + 70, ellipse_y - 8), ISSUE_TITLE, font(24, True), TXT, "lm")
        T(d, (cx0 + 70, ellipse_y + 24), "#1 opened by a teammate", font(18), MUTED, "lm")
    else:
        T(d, (cx0 + 24, cy0 + 40), ISSUE_TITLE, font(26, True), TXT, "lm")
        T(d, (cx0 + 24, cy0 + 84), "#1", font(26), MUTED, "lm")
        chip(d, cx0 + 90, cy0 + 62, "Open", GREEN, font(20, True), h=36)
        T(d, (cx0 + 24, cy0 + 150), "As an operator, I want a \"New Chat\" option in the chat", font(20), TXT, "lm")
        T(d, (cx0 + 24, cy0 + 180), "window so older context is erased and I can start with", font(20), TXT, "lm")
        T(d, (cx0 + 24, cy0 + 210), "a new prompt.", font(20), TXT, "lm")
        T(d, (cx0 + 24, cy0 + 270), "Acceptance criteria", font(22, True), TXT, "lm")
        for k, s in enumerate(CRITERIA):
            check(d, cx0 + 24, cy0 + 304 + k * 80, s, done=False, f=font(19), w=780)
        if prog(t, t_issue, 0.4) > 0:
            d.rectangle((cx0 + 8, cy0 + 20, cx0 + 14, cy0 + 110), fill=AMBER)
    if t >= t_view:
        chip(d, 90, 878, "BOB READS THE ISSUE DIRECTLY FROM GITHUB", IBM, font(20, True), h=40)
    bx0, by0, bx1, by1 = bob_panel(d, (1030, 70, 1860, 930), "AGENT")
    pt = typed("Pick up issue 1.", t - t_ask, 18)
    if t >= t_ask:
        box(d, (bx0 + 16, by0 + 10, bx1 - 16, by0 + 62), fill=mix(BG, IBM_DARK, 0.8), rad=12)
        T(d, (bx0 + 36, by0 + 36), pt, font(24), WHITE, "lm")
    lines = [("$ gh issue view 1", TXT, t_view), (f"title:  {ISSUE_TITLE[:44]}…", MUTED, t_view + 1.0),
             ("state:  OPEN", GREEN, t_view + 1.4), ("labels: enhancement", MUTED, t_view + 1.8)]
    f = font(19, mono=True)
    for k, (s, col, ts) in enumerate(lines):
        if t >= ts:
            T(d, (bx0 + 20, by0 + 100 + k * 30), s if not s.startswith("$ ") else typed(s, t - ts, 40), f, col)
    if t >= t_crit:
        T(d, (bx0 + 20, by0 + 250), "Acceptance criteria", font(22, True), TXT, "lm")
        for k, s in enumerate(CRITERIA):
            check(d, bx0 + 20, by0 + 280 + k * 74, s, done=t >= t_crit + 0.5 + k * 0.7, f=font(20), w=640)
    if t >= t_branch:
        T(d, (bx0 + 20, by1 - 140), typed("$ git checkout -b feature/new-chat-button", t - t_branch, 40), f, TXT, "lm")
    if t >= t_branch + 1.3:
        T(d, (bx0 + 20, by1 - 108), "Switched to a new branch 'feature/new-chat-button'", f, GREEN, "lm")
        chip(d, bx0 + 20, by1 - 70, "branch: feature/new-chat-button", CYAN, font(20, True), h=42)
    p = prog(t, c("No copy-pasting"), 0.5)
    if p > 0:
        T(d, (bx0 + 20, by1 - 190), "No copy-pasting tickets into a chat window.", font(22, True), mix(PANEL, WHITE, p), "lm")


# Scene 10: implement the feature - Sat 14 Nov 2026 18:20 CET
DIFFS = {
    "templates/index.html": [("  <div class=\"chat-header\">", MUTED), ("    <select id=\"modelSelect\">…</select>", MUTED),
                             ("+   <button id=\"newChatBtn\" class=\"btn\">New Chat</button>", GREEN),
                             ("  </div>", MUTED)],
    "static/js/app.js": [("+ document.getElementById(\"newChatBtn\")", GREEN), ("+   .addEventListener(\"click\", () => {", GREEN),
                         ("+     conversationHistory = [];", GREEN), ("+     chatStream.innerHTML = welcomeHTML;", GREEN),
                         ("+     input.value = \"\"; input.focus();", GREEN), ("+   });", GREEN)],
    "tests/test_ui.py": [("+ def test_index_has_new_chat_button(client):", GREEN),
                         ("+     html = client.get(\"/\").get_data(as_text=True)", GREEN),
                         ("+     assert 'id=\"newChatBtn\"' in html", GREEN)],
}


def s10(img, d, t):
    c = K(10)
    paint_backdrop(img)
    t_files, t_btn, t_hist = c("finds the right files"), c("adds the button"), c("clears the conversation history")
    t_welcome, t_test, t_suite = c("restores the welcome screen"), c("It adds a test"), c("runs the whole suite")
    t_green, t_fail = c("All green"), c("If a test had failed")
    # editor
    cx0, cy0, cx1, cy1 = win(d, (60, 70, 1130, 610), "Editor: feature/new-chat-button", fill=CODE_BG)
    names = ["templates/index.html", "static/js/app.js", "tests/test_ui.py"]
    shown = [n for n, ts in zip(names, [t_files, t_files, t_test]) if t >= ts]
    active = names[2] if t >= t_test else names[1] if t >= t_hist else names[0]
    x = cx0 + 10
    for n in shown:
        f = font(19, n == active, True)
        w = int(f.getlength(n)) + 36
        d.rectangle((x, cy0, x + w, cy0 + 44), fill=PANEL2 if n == active else CODE_BG)
        T(d, (x + w / 2, cy0 + 22), n, f, TXT if n == active else MUTED, "mm")
        x += w + 4
    if t >= t_files and t < t_btn:
        T(d, ((cx0 + cx1) / 2, cy0 + 200), "Locating the page template and the front-end script…", font(26), MUTED, "mm")
    if t >= t_btn:
        show = DIFFS[active]
        if active == names[0]:
            n_vis = 4
        else:
            ref = t_hist if active == names[1] else t_test
            n_vis = min(len(show), 1 + int((t - ref) / 0.6))
        rows = [(s, col, (14, 48, 28) if s.startswith("+") else None) for s, col in show[:n_vis]]
        code(d, (cx0 + 10, cy0 + 70, cx1 - 10, cy1), rows, fs=22, lh=40)
    # terminal
    lines = [("$ ./run.sh test", TXT, t_suite), ("collected 17 items", MUTED, t_suite + 1.0)]
    for k, (nm, n) in enumerate([("test_config.py", 2), ("test_pentest_guard.py", 5), ("test_prompt_cache.py", 4),
                                 ("test_hexstrike_tools.py", 2), ("test_agent.py", 2), ("test_reporter.py", 1), ("test_ui.py", 1)]):
        lines.append((f"tests/{nm} {'.' * n}", GREEN, t_suite + 1.6 + k * 0.4))
    lines.append(("==== 17 passed in 2.48s ====", GREEN, t_green))
    term(d, (60, 630, 1130, 930), lines, t, "terminal: pentest-agent", 18, 26)
    if t >= t_green:
        chip(d, 860, 880, "ALL TESTS PASSING", GREEN, font(22, True), h=44)
    # acceptance
    bx0, by0, bx1, by1 = bob_panel(d, (1160, 70, 1860, 470), "AGENT")
    T(d, (bx0 + 18, by0 + 8), "Acceptance criteria", font(22, True), TXT, "lm")
    times = [t_btn + 1.0, t_hist + 1.5, t_welcome, t_green]
    for k, s in enumerate(CRITERIA):
        check(d, bx0 + 18, by0 + 36 + k * 62, s, done=t >= times[k], f=font(18), w=560)
    if t >= t_fail:
        T(d, (bx0 + 18, by1 - 20), "If a test fails: read, fix, re-run.", font(18, True), AMBER, "lm")
    # browser clip
    bx0, by0, bx1, by1 = chrome(d, "http://127.0.0.1:5000", (1160, 490, 1860, 930))
    d.rectangle((bx0, by0, bx1, by0 + 50), fill=PANEL2)
    T(d, (bx0 + 16, by0 + 25), "Pentest Agent", font(20, True), TXT, "lm")
    if t >= t_btn + 0.8:
        chip(d, bx1 - 160, by0 + 7, "+ New Chat", IBM, font(16, True), h=36)
    t_click = t_welcome + 0.6
    if t < t_click:
        for k, s in enumerate(["Run a health check on the HexStrike server", "Server healthy. 149+ tools available."]):
            box(d, (bx0 + 20 + k * 90, by0 + 70 + k * 80, bx1 - 20 - (1 - k) * 90, by0 + 130 + k * 80),
                fill=mix(BG, IBM_DARK, 0.8) if k == 0 else PANEL2, rad=12)
            T(d, (bx0 + 40 + k * 90, by0 + 100 + k * 80), s, font(16), WHITE, "lm")
    else:
        T(d, ((bx0 + bx1) / 2, by0 + 150), "Welcome. How can I help?", font(26, True), TXT, "mm")
        T(d, ((bx0 + bx1) / 2, by0 + 190), "New conversation, fresh context.", font(18), MUTED, "mm")
    if t_btn + 0.8 <= t < t_click + 0.4:
        cx_, cy_ = bx1 - 60, by0 + 25
        d.polygon([(cx_, cy_), (cx_ + 4, cy_ + 22), (cx_ + 10, cy_ + 14), (cx_ + 18, cy_ + 18)], fill=WHITE)


# Scene 11: commit, push, pull request - Sat 14 Nov 2026 18:20 CET
def s11(img, d, t):
    c = K(11)
    paint_backdrop(img)
    t_commit, t_push, t_pr = c("commits with"), c("pushes the branch"), c("opens a pull request")
    t_sum, t_files, t_res, t_chk = c("summary"), c("files changed"), c("test results"), c("reviewer checklist")
    t_ready, t_human, t_prot = c("merge-ready"), c("A human still reviews"), c("Bob never bypasses")
    lines = [("$ git add -A", TXT, t_commit),
             ('$ git commit -m "feat(chat): add New Chat button to reset conversation context (#1)"', TXT, t_commit + 0.8),
             ("[feature/new-chat-button 9d41b7e] 3 files changed, 21 insertions(+)", MUTED, t_commit + 4.2),
             ("$ git push -u origin feature/new-chat-button", TXT, t_push),
             ("remote: Create a pull request for 'feature/new-chat-button'", MUTED, t_push + 1.4),
             ('$ gh pr create --title "feat(chat): New Chat button" --body-file pr_body.md', TXT, t_pr),
             (f"https://github.com/{REPO}/pull/2", GREEN, t_pr + 2.0)]
    term(d, (60, 70, 950, 560), lines, t, "terminal: pentest-agent", 17, 28)
    # merge-ready checklist
    win(d, (60, 580, 950, 930), "Merge-ready checklist", fill=PANEL)
    items = [("LINKED TO ISSUE #1", t_ready), ("TESTS PASSING", t_ready + 0.9), ("CLEAR DESCRIPTION", t_ready + 1.8),
             ("NO SECRETS IN DIFF", t_ready + 2.7), ("HUMAN REVIEW REQUIRED", t_human)]
    for k, (s, ts) in enumerate(items):
        check(d, 90, 650 + k * 54, s, done=t >= ts, col=AMBER if k == 4 else GREEN, f=font(24, True))
    # PR page
    cx0, cy0, cx1, cy1 = gh_page(d, (980, 70, 1860, 930), f"github.com/{REPO}/pull/" + ("2" if t >= t_pr + 2.0 else ""),
                                 REPO, "Pull requests")
    if t < t_pr + 2.0:
        T(d, ((cx0 + cx1) / 2, cy0 + 120), "No open pull requests", font(26), MUTED, "mm")
    else:
        T(d, (cx0 + 24, cy0 + 36), "feat(chat): New Chat button", font(28, True), TXT, "lm")
        T(d, (cx0 + 24, cy0 + 80), "#2", font(24), MUTED, "lm")
        chip(d, cx0 + 80, cy0 + 60, "Open", GREEN, font(18, True), h=34)
        chip(d, cx0 + 180, cy0 + 60, "Closes #1", PURPLE, font(18, True), h=34)
        y = cy0 + 130
        if t >= t_sum:
            T(d, (cx0 + 24, y), "Summary", font(22, True), TXT, "lm")
            T(d, (cx0 + 24, y + 34), "Adds a New Chat button that clears the conversation", font(18), MUTED, "lm")
            T(d, (cx0 + 24, y + 60), "history and restores the welcome screen.", font(18), MUTED, "lm")
        if t >= t_files:
            T(d, (cx0 + 24, y + 100), "Files changed", font(22, True), TXT, "lm")
            for k, (nm, ad) in enumerate([("templates/index.html", "+1"), ("static/js/app.js", "+6"), ("tests/test_ui.py", "+14")]):
                T(d, (cx0 + 24, y + 134 + k * 26), nm, font(18, mono=True), TXT, "lm")
                T(d, (cx0 + 380, y + 134 + k * 26), ad, font(18, mono=True), GREEN, "lm")
        if t >= t_res:
            T(d, (cx0 + 24, y + 224), "Test results", font(22, True), TXT, "lm")
            T(d, (cx0 + 24, y + 254), "17 passed", font(20, mono=True), GREEN, "lm")
        if t >= t_chk:
            T(d, (cx0 + 24, y + 300), "Reviewer checklist", font(22, True), TXT, "lm")
            for k, s in enumerate(["Button placement matches the issue", "History cleared on click", "Tests cover the new button"]):
                check(d, cx0 + 24, y + 332 + k * 36, s, done=False, f=font(18))
    p = prog(t, t_prot, 0.5)
    if p > 0:
        box(d, (990, 836, 1850, 922), fill=mix(BG, IBM_DARK, 0.9 * p), outline=mix(BG, IBM, p), w=2, rad=14)
        T(d, (1420, 862), "You review. You merge.", font(28, True), mix(BG, WHITE, p), "mm")
        T(d, (1420, 898), "Your branch protections stay in charge.", font(22), mix(BG, WHITE, p), "mm")


USE_CASES = [
    ("GREENFIELD", "Brief → tested scaffold", "An afternoon, not a sprint", "One:", GREEN),
    ("BACKLOG BURN-DOWN", "Issue → reviewed pull request", "Teammates review. Bob does the legwork", "Two:", IBM),
    ("HARDENING", "Provider error → 5 protection layers", "Plus tests and a README chapter", "Three:", AMBER),
    ("INTEGRATION", "140+ security tools through MCP", "One agent, one tool layer", "Four:", CYAN),
    ("AUDIT TRAIL", "Every task leaves a saved record", "Prompt and timestamp, kept on disk", "And five", PURPLE),
]
LAYERS = ["Tool schema minification", "Query-aware tool selection", "Tool output truncation",
          "Message history compaction", "Automatic retry on provider limit"]
TOOLS = ["nmap", "nuclei", "gobuster", "sqlmap", "hydra", "trivy", "ffuf", "nikto", "masscan", "wpscan", "amass",
         "httpx", "subfinder", "checkov", "prowler", "+130 more"]


# Scene 12: use cases - Sat 14 Nov 2026 18:20 CET
def s12(img, d, t):
    c = K(12)
    times = [c(u[3], -0.2) for u in USE_CASES]
    if t < times[0]:
        img.paste(zoomed(backlog_layer(60 + t, 0.82), 1.07))
        d = ImageDraw.Draw(img)
        nameplate(d, t + 6, 0)
        T(d, (960, 360), "Where does this fit in your organization?", font(66, True), TXT, "mm")
        return
    paint_backdrop(img)
    active = max(k for k in range(5) if t >= times[k])
    for k, (h, a, b, _, col) in enumerate(USE_CASES):
        if t < times[k]:
            continue
        y = 110 + k * 160
        on = k == active
        box(d, (70, y, 740, y + 140), fill=mix(BG, col, 0.2 if on else 0.06), outline=col if on else LINE, w=3 if on else 2, rad=16)
        T(d, (112, y + 70), str(k + 1), font(56, True), col, "mm")
        T(d, (160, y + 54), h, font(30, True), TXT if on else MUTED, "lm")
        T(d, (160, y + 98), a, font(20), MUTED, "lm")
    h, a, b, _, col = USE_CASES[active]
    ta = t - times[active]
    box(d, (790, 110, 1850, 910), fill=PANEL, outline=col, w=3, rad=20)
    T(d, (840, 170), h, font(60, True), col, "lm")
    T(d, (840, 235), a, font(34, True), TXT, "lm")
    T(d, (840, 280), b, font(26), MUTED, "lm")
    if active == 0:
        for k, s in enumerate(["empty repository", "plan approved", "code + tests written", "16 tests passing"]):
            check(d, 850, 360 + k * 70, s, done=ta > 0.6 + k * 0.9, f=font(30))
    elif active == 1:
        for k, (s, col2) in enumerate([("Issue #1: New Chat button", GREEN), ("Branch + code + tests", IBM), ("Pull request #2, ready for review", AMBER)]):
            if ta > 0.4 + k * 1.0:
                box(d, (850, 360 + k * 110, 1800, 450 + k * 110), fill=mix(PANEL, col2, 0.2), outline=col2, w=2, rad=12)
                T(d, (880, 405 + k * 110), s, font(30, True), TXT, "lm")
    elif active == 2:
        box(d, (850, 340, 1800, 420), fill=(40, 18, 22), outline=RED, w=2, rad=12)
        T(d, (880, 380), "400: request exceeds the 100,000 character limit", font(26, True, True), TXT, "lm")
        for k, s in enumerate(LAYERS):
            if ta > 1.0 + k * 0.8:
                check(d, 860, 460 + k * 60, s, done=True, col=AMBER, f=font(28))
        if ta > 5.5:
            T(d, (860, 800), "+ unit tests   + README chapter", font(28, True), GREEN, "lm")
    elif active == 3:
        x, y = 850, 360
        for k, s in enumerate(TOOLS):
            if ta > 0.2 + k * 0.18:
                f = font(26, True)
                w = int(f.getlength(s)) + 40
                if x + w > 1800:
                    x, y = 850, y + 70
                chip(d, x, y, s, CYAN if k < 15 else AMBER, f, h=52)
                x += w + 16
    else:
        win(d, (850, 340, 1800, 820), "task-outcomes/ibm_bob_client_demo_script.txt", fill=CODE_BG)
        for k, (s, col2) in enumerate([("PROMPT: Create a comprehensive 7-minute video script…", TXT),
                                      ("DATE: Sat 14 Nov 2026 17:56:23 CET", MUTED), ("", TXT), ("OUTCOME", AMBER),
                                      ("- v2 script created, approach B applied", TXT), ("- 14 scenes, ~760 spoken words", TXT),
                                      ("- status: awaiting approval", TXT)]):
            if ta > 0.4 + k * 0.35:
                T(d, (880, 420 + k * 50), s, font(22, mono=True), col2, "lm")


# Scene 13: call to action - Sat 14 Nov 2026 18:20 CET
OPTIONS = [("HANDS-ON WORKSHOP", ["Half day", "Your team", "Your repository"], GREEN, "A hands-on workshop"),
           ("DEEPER PRODUCT DIVE", ["Architecture", "Security model", "Governance fit"], IBM, "A deeper product dive"),
           ("PROOF OF EXPERIENCE", ["One real issue from your backlog", "Taken to a pull request together", "In your GitHub"],
            AMBER, "Or a Proof of Experience")]


def s13(img, d, t):
    c = K(13)
    img.paste(zoomed(backlog_layer(70 + t, 0.85), 1.07))
    d = ImageDraw.Draw(img)
    t_end = c("Tell me which fits")
    T(d, (960, 130), "Choose your next step", font(64, True), TXT, "mm")
    if t < t_end:
        nameplate(d, t + 6, 0)
    for k, (h, lines, col, ph) in enumerate(OPTIONS):
        p = prog(t, c(ph, -0.3), 0.6)
        if p <= 0:
            continue
        x = 110 + k * 580 + int((1 - p) * 400)
        box(d, (x, 230, x + 540, 640), fill=mix(BG, col, 0.14 * p), outline=mix(BG, col, p), w=3, rad=20)
        T(d, (x + 30, 290), h, font(34, True), mix(BG, col, p), "lm")
        for j, ln in enumerate(lines):
            for m, part in enumerate(wrap(ln, font(28), 480)):
                T(d, (x + 30, 370 + j * 60 + m * 30), part, font(28), mix(BG, TXT, p), "lm")
    p = prog(t, t_end, 0.8)
    if p > 0:
        box(d, (360, 700, 1560, 930), fill=mix(BG, (10, 16, 26), p), outline=mix(BG, IBM, p), w=3, rad=22)
        T(d, (960, 760), "Bobby, Enterprise Sales", font(44, True), mix(BG, WHITE, p), "mm")
        T(d, (960, 820), "[EMAIL]   ·   [BOOKING LINK]", font(34), mix(BG, TXT, p), "mm")
        box(d, (860, 868, 892, 900), fill=mix(BG, IBM_DARK, p))
        T(d, (910, 884), "IBM Bob", font(30, True), mix(BG, WHITE, p), "lm")
        T(d, (960, 950), "Made with IBM Bob", font(18), mix(BG, MUTED, p), "mm")
