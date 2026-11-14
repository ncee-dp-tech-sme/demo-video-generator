# Scenes 0-6 of the IBM Bob client demo (seller intro, pain points, value, Part 1: Build).
#
# Change log
# Sat 14 Nov 2026 18:10 CET - Initial version.

import math

from PIL import Image, ImageDraw

import demo_common as C
from bob_ui import (AMBER, BG, BLACK, BLUE, CODE_BG, CYAN, GH_BG, GH_LINE, GREEN, H, IBM, IBM_DARK, K, LINE,
                    MUTED, PANEL, PANEL2, PURPLE, RED, T, TXT, W, WHITE, blink, bob_panel, box, callout,
                    check, chip, clamp, code, font, gh_page, mix, nameplate, paint_backdrop, prog, term,
                    title_card, typed, win, wrap, zoomed)
from build_video import chrome

ISSUES = [
    ("Export assessment report as PDF", "#32", "feature", BLUE),
    ("Prompt cache: delete a single entry", "#31", "feature", BLUE),
    ("Errors on very large prompts", "#30", "bug", RED),
    ("Model selector: remember last choice", "#29", "feature", BLUE),
    ("Settings page: add live health check", "#28", "feature", BLUE),
    ("Document backup and restore in README", "#27", "docs", AMBER),
    ("Consent record misses target scope", "#26", "bug", RED),
    ("Audit tab: filter by risk level", "#25", "feature", BLUE),
    ("Upgrade outdated dependencies", "#24", "chore", MUTED),
    ("Trim long tool output in chat", "#23", "feature", BLUE),
    ("Dark mode for the report view", "#22", "feature", BLUE),
    ("Add smoke test for run.sh start", "#21", "chore", MUTED),
]


# Dimmed GitHub-style backlog used behind the name plate - Sat 14 Nov 2026 18:10 CET
def backlog_layer(t, dim=0.55):
    layer = Image.new("RGB", (W, H), GH_BG)
    ld = ImageDraw.Draw(layer)
    ld.rectangle((300, 0, 1620, H), fill=(15, 19, 26), outline=GH_LINE)
    T(ld, (340, 70), "Issues", font(40, True), TXT, "lm")
    chip(ld, 480, 46, "47 Open", GREEN, font(22, True), h=44)
    off = t * 14
    for k in range(24):
        y = 140 + k * 92 - off
        if y < 100 or y > H:
            continue
        title, num, label, col = ISSUES[k % len(ISSUES)]
        ld.line((300, y - 6, 1620, y - 6), fill=GH_LINE)
        ld.ellipse((340, y + 18, 366, y + 44), outline=GREEN, width=3)
        T(ld, (390, y + 20), title, font(28, True), TXT, "lm")
        T(ld, (390, y + 58), f"{num} opened by a teammate", font(20), MUTED, "lm")
        chip(ld, 1440, y + 14, label, col, font(18, True), h=36)
    return Image.blend(layer, Image.new("RGB", (W, H), BLACK), dim)


# Scene 0: cold open, backlog + name plate - Sat 14 Nov 2026 18:10 CET
def s0(img, d, t):
    c = K(0)
    dur = C.TL[0]["end"] - C.TL[0]["start"]
    img.paste(zoomed(backlog_layer(t), 1 + 0.07 * t / dur))
    d = ImageDraw.Draw(img)
    nameplate(d, t, 1.0)
    p = prog(t, c("What's missing"), 0.5)
    if p > 0:
        y = 330
        f = font(40, True)
        items = [(110, 560, "We should build this", IBM), (720, 110, "?", RED), (880, 640, "Tested, reviewed, merged", GREEN)]
        for k, (x, w, txt, col) in enumerate(items):
            a = clamp(p * 3 - k)
            if a > 0:
                box(d, (x, y, x + w, y + 90), fill=mix(BG, col, 0.2 * a), outline=mix(BG, col, a), w=3, rad=45)
                T(d, (x + w / 2, y + 45), txt, f, mix(BG, col, a), "mm")
        d.line((674, y + 45, 716, y + 45), fill=MUTED, width=3)
        d.line((834, y + 45, 876, y + 45), fill=MUTED, width=3)


# Pain card frame: number chip + heading - Sat 14 Nov 2026 18:10 CET
def pain_frame(img, d, n, title, sub, col):
    paint_backdrop(img)
    box(d, (110, 90, 184, 164), fill=mix(BG, col, 0.25), outline=col, w=3, rad=37)
    T(d, (147, 127), str(n), font(44, True), col, "mm")
    T(d, (214, 112), title, font(68, True), TXT, "lm")
    T(d, (214, 168), sub, font(30), MUTED, "lm")


# Scene 1: three pain points - Sat 14 Nov 2026 18:10 CET
def s1(img, d, t):
    c = K(1)
    a, b, g = c("Boilerplate"), c("Context switching"), c("And governance")
    if t < a - 0.05:
        img.paste(zoomed(backlog_layer(20 + t, 0.62), 1.07))
        d = ImageDraw.Draw(img)
        T(d, (960, 420), "Three things slow you down", font(78, True), TXT, "mm")
        return
    if t < b - 0.05:
        pain_frame(img, d, 1, "BOILERPLATE", "Days of scaffolding before the first line of real business logic", AMBER)
        tree = ["my-service/", "  config/", "  core/", "  templates/", "  static/", "  tests/", "  docs/", "  scripts/",
                "  .env.example", "  .gitignore", "  Dockerfile", "  README.md"]
        box(d, (110, 250, 900, 900), fill=CODE_BG, outline=LINE, w=2, rad=14)
        for k, s in enumerate(tree):
            if t - a > 0.3 + k * 0.4:
                T(d, (150, 290 + k * 48), s, font(30, mono=True), AMBER if s.endswith("/") else TXT, "lm")
                T(d, (620, 290 + k * 48), "empty", font(22, mono=True), MUTED, "lm")
        for k in range(3):
            on = t - a > 1.5 + k * 3.0
            x = 1000 + k * 280
            box(d, (x, 380, x + 250, 500), fill=mix(PANEL, AMBER, 0.25 if on else 0.0), outline=AMBER if on else LINE, w=3, rad=16)
            T(d, (x + 125, 440), f"Day {k + 1}", font(44, True), AMBER if on else MUTED, "mm")
        T(d, (1000, 600), "…and still no business logic.", font(46, True), TXT, "lm")
        T(d, (1000, 670), "Config, structure, tooling, docs:", font(30), MUTED, "lm")
        T(d, (1000, 712), "the same groundwork, rebuilt every time.", font(30), MUTED, "lm")
    elif t < g - 0.05:
        pain_frame(img, d, 2, "CONTEXT SWITCHING", "Leave the editor to read, run, write and open", IBM)
        cx, cy, r = 700, 590, 270
        nodes = ["Read the issue", "Edit code", "Run tests", "Write commit message", "Open pull request"]
        pts = [(cx + r * math.sin(2 * math.pi * k / 5), cy - r * math.cos(2 * math.pi * k / 5)) for k in range(5)]
        order = [0, 2, 4, 1, 3, 0]
        for k in range(5):
            d.line((*pts[order[k]], *pts[order[k + 1]]), fill=(40, 60, 100), width=3)
        tt = ((t - b) * 0.45) % 5
        seg = int(tt)
        fr = tt - seg
        p0, p1 = pts[order[seg]], pts[order[seg + 1]]
        px, py = p0[0] + (p1[0] - p0[0]) * fr, p0[1] + (p1[1] - p0[1]) * fr
        d.ellipse((px - 14, py - 14, px + 14, py + 14), fill=AMBER)
        for k, (x, y) in enumerate(pts):
            box(d, (x - 120, y - 34, x + 120, y + 34), fill=PANEL2, outline=IBM, w=2, rad=17)
            T(d, (x, y), nodes[k], font(22, True), TXT, "mm")
        T(d, (1180, 470), "Every hop costs focus.", font(56, True), TXT, "lm")
        T(d, (1180, 540), "Five tools, five contexts,", font(32), MUTED, "lm")
        T(d, (1180, 584), "for one small change.", font(32), MUTED, "lm")
    else:
        pain_frame(img, d, 3, "GOVERNANCE AT REVIEW TIME", "Standards checked last, when fixing costs the most", RED)
        gh_page(d, (110, 250, 1250, 900), "github.com/acme/service/pull/42", None)
        T(d, (140, 330), "feat: add export endpoint", font(36, True), TXT, "lm")
        T(d, (140, 370), "#42 opened 2 days ago", font(20), MUTED, "lm")
        chip(d, 840, 310, "Changes requested", RED, font(22, True), h=44)
        notes = ["config.py: API key is hard-coded", "app.py: service binds to 0.0.0.0", "No tests for the new endpoint",
                 "Missing .gitignore entry for .env"]
        for k, s in enumerate(notes):
            if t - g > 0.6 + k * 1.1:
                box(d, (140, 420 + k * 110, 1220, 505 + k * 110), fill=(30, 18, 22), outline=RED, w=2, rad=10)
                T(d, (170, 462 + k * 110), s, font(30), TXT, "lm")
        T(d, (1330, 480), "Found at review time.", font(52, True), TXT, "lm")
        T(d, (1330, 550), "Rework, re-review, wait.", font(34), MUTED, "lm")


# IDE shell with explorer, editor placeholder and Bob panel - Sat 14 Nov 2026 18:10 CET
def ide_shell(d, rect, t, title="IDE: empty-repo"):
    x0, y0, x1, y1 = rect
    cx0, cy0, cx1, cy1 = win(d, rect, title, fill=CODE_BG)
    d.rectangle((cx0, cy0, cx0 + 250, cy1), fill=(14, 20, 29))
    T(d, (cx0 + 18, cy0 + 24), "EXPLORER", font(16, True), MUTED, "lm")
    T(d, (cx0 + 18, cy0 + 64), "empty-repo", font(20, mono=True), TXT, "lm")
    T(d, (cx0 + 36, cy0 + 100), "(no files yet)", font(18, mono=True), MUTED, "lm")
    T(d, ((cx0 + 250 + cx1 - 400) / 2, (cy0 + cy1) / 2), "Empty editor", font(30), (70, 82, 98), "mm")
    bp = bob_panel(d, (cx1 - 400, y0 + 42, x1 - 2, y1 - 2), "AGENT")
    box(d, (bp[0] + 16, bp[3] - 74, bp[2] - 16, bp[3] - 16), fill=PANEL2, outline=LINE, w=2, rad=10)
    T(d, (bp[0] + 32, bp[3] - 45), "Ask Bob" + ("|" if blink(t) else ""), font(20), MUTED, "lm")
    T(d, (bp[0] + 18, bp[1] + 20), "How can I help you build today?", font(22), TXT)
    return bp


# Scene 2: value proposition pillars - Sat 14 Nov 2026 18:10 CET
def s2(img, d, t):
    c = K(2)
    if t < 1.2:
        img.paste(zoomed(backlog_layer(40 + t, 0.62), 1.07))
        d = ImageDraw.Draw(img)
        nameplate(d, t + 6, 0)
        return
    paint_backdrop(img)
    ide_shell(d, (60, 70, 1230, 900), t)
    pillars = [("PLANS FIRST", "Proposes the architecture before writing code", "plans before it codes"),
               ("FOLLOWS YOUR RULES", "Applies your team's standards while it writes", "follows your team's rules"),
               ("RUNS THE TESTS", "Builds, runs and validates its own work", "runs the tests itself"),
               ("MERGE-READY PRs", "Commits, pushes and opens the pull request", "pull request you can")]
    cols = [PURPLE, IBM, GREEN, AMBER]
    for k, (h, sub, ph) in enumerate(pillars):
        p = prog(t, c(ph, -0.3), 0.5)
        if p <= 0:
            continue
        x, y = 1270 + int((1 - p) * 60), 90 + k * 195
        box(d, (x, y, 1860, y + 170), fill=mix(BG, cols[k], 0.15 * p), outline=mix(BG, cols[k], p), w=3, rad=16)
        d.rectangle((x, y + 14, x + 8, y + 156), fill=cols[k])
        T(d, (x + 34, y + 54), h, font(36, True), mix(BG, TXT, p), "lm")
        for j, ln in enumerate(wrap(sub, font(24), 520)):
            T(d, (x + 34, y + 102 + j * 30), ln, font(24), mix(BG, MUTED, p), "lm")
    p = prog(t, c("You stay the reviewer"), 0.5)
    if p > 0:
        T(d, (960, 940), "You review. Bob does the legwork.", font(46, True), mix(BG, WHITE, p), "mm")


# Scene 3: Part 1 title - Sat 14 Nov 2026 18:10 CET
def s3(img, d, t):
    title_card(img, d, t, 1, "BUILD", "Empty repository  →  tested application", 0)


BRIEF = ["MCP server on localhost:8888", "OpenAI-compatible chat backend", "Selectable model, sensible default",
         "Authorization prompt before pentest activity", "Prompt cache with audit and selective delete",
         "Markdown and PDF export"]
PLAN = [("config.py", "settings, model catalog, default model"), ("core/pentest_guard.py", "authorization and consent guard"),
        ("core/prompt_cache.py", "SQLite audit cache, selective delete"), ("core/hexstrike_tools.py", "MCP tool layer"),
        ("core/agent.py", "multi-turn agent loop"), ("core/reporter.py", "Markdown and PDF reports"),
        ("app.py + templates/", "web UI and REST API")]


# Scene 4: Plan mode - Sat 14 Nov 2026 18:10 CET
def s4(img, d, t):
    c = K(4)
    paint_backdrop(img)
    term(d, (60, 70, 760, 330), [("$ ls -la", TXT, 0.4), ("total 0", MUTED, 1.4),
                                 ("drwxr-xr-x   2 bobby  staff   64 .", MUTED, 1.5),
                                 ("drwxr-xr-x  12 bobby  staff  384 ..", MUTED, 1.6)], t, "terminal: empty-repo", 18, 26)
    cx0, cy0, cx1, cy1 = win(d, (60, 350, 760, 800), "Explorer", fill=CODE_BG)
    T(d, (cx0 + 20, cy0 + 28), "pentest-agent/", font(22, mono=True), TXT, "lm")
    T(d, (cx0 + 40, cy0 + 68), "(empty repository)", font(20, mono=True), MUTED, "lm")
    callout(d, (60, 830), "PLAN MODE: nothing is written until you approve", PURPLE, t, c("Plan mode"), font(22, True))
    bx0, by0, bx1, by1 = bob_panel(d, (800, 70, 1860, 930), "PLAN")
    T(d, (bx0 + 24, by0 + 14), "BRIEF", font(18, True), MUTED, "lm")
    box(d, (bx0 + 16, by0 + 34, bx1 - 16, by0 + 304), fill=PANEL2, outline=LINE, w=2, rad=10)
    times = [c("Here's the brief"), c("OpenAI-compatible"), c("OpenAI-compatible", 1.6), c("explicit authorization"),
             c("full audit trail"), c("One paragraph")]
    for k, s in enumerate(BRIEF):
        p = prog(t, times[k], 0.4)
        if p > 0:
            T(d, (bx0 + 40, by0 + 66 + k * 40), "•  " + s, font(24), mix(PANEL2, AMBER if k in (0, 1, 3, 4, 5) else TXT, p), "lm")
    T(d, (bx0 + 24, by0 + 330), "PROPOSED PLAN", font(18, True), PURPLE, "lm")
    keys = ["configuration", "an authorization guard", "a prompt cache", "a tool layer", "an agent loop", "a reporter",
            "a web UI"]
    for k, (fn, desc) in enumerate(PLAN):
        p = prog(t, c(keys[k], -0.2), 0.4)
        if p > 0:
            y = by0 + 360 + k * 46
            box(d, (bx0 + 16, y, bx1 - 16, y + 38), fill=mix(BG, PURPLE, 0.12 * p), outline=mix(BG, PURPLE, p), w=2, rad=10)
            T(d, (bx0 + 36, y + 19), f"{k + 1}", font(24, True), mix(BG, PURPLE, p), "lm")
            T(d, (bx0 + 76, y + 19), fn, font(22, True, True), mix(BG, TXT, p), "lm")
            T(d, (bx0 + 450, y + 19), desc, font(20), mix(BG, MUTED, p), "lm")
    y = by1 - 70
    if prog(t, c("I review it"), 0.4) > 0:
        chip(d, bx0 + 20, y, "default model: gpt-4.1-mini", CYAN, font(22, True), h=48)
    ap = prog(t, c("I approve"), 0.35)
    col = mix(PURPLE, GREEN, ap)
    box(d, (bx1 - 330, y, bx1 - 20, y + 52), fill=mix(BG, col, 0.35 if ap < 1 else 0.9), outline=col, w=3, rad=26)
    T(d, (bx1 - 175, y + 26), "Plan approved" if ap > 0.5 else "Approve plan", font(24, True), WHITE if ap > 0.5 else col, "mm")
    if ap > 0.5:
        d.line((bx1 - 308, y + 28, bx1 - 300, y + 36), fill=WHITE, width=4)
        d.line((bx1 - 300, y + 36, bx1 - 288, y + 18), fill=WHITE, width=4)


FILES = [(".env.example", 1), (".gitignore", 1), ("README.md", 1), ("app.py", 1), ("config.py", 1),
         ("requirements.txt", 1), ("run.sh", 1), ("core/", 1), ("agent.py", 2), ("hexstrike_tools.py", 2),
         ("pentest_guard.py", 2), ("prompt_cache.py", 2), ("reporter.py", 2), ("templates/", 1), ("static/", 1),
         ("tests/", 1)]
ZOOMS = {
    "env": (".env.example", "SECRETS OUT OF CODE", [
        ("# Copy to .env and fill in. Never commit .env", MUTED), ("ONEMIN_API_KEY=your-api-key-here   # HashiCorpIgnore", AMBER),
        ("HEXSTRIKE_SERVER_URL=http://127.0.0.1:8888", TXT), ("DEFAULT_MODEL=gpt-4.1-mini", TXT), ("LOG_LEVEL=INFO", TXT)]),
    "host": ("app.py", "LOCALHOST ONLY", [
        ("from config import HOST, PORT", TXT), ("", TXT), ("if __name__ == \"__main__\":", TXT),
        ("    app.run(host=\"127.0.0.1\", port=PORT)", AMBER)]),
    "git": (".gitignore", "SENSITIVE FILES EXCLUDED", [
        (".env", AMBER), (".venv/", AMBER), ("__pycache__/", TXT), ("data/*.db", AMBER), ("reports/*.pdf", TXT),
        ("logs/*.log", TXT)]),
}


# Scene 5: Agent mode scaffolding - Sat 14 Nov 2026 18:10 CET
def s5(img, d, t):
    c = K(5)
    paint_backdrop(img)
    n_files = len(FILES)
    t_i = [1.0 + i * 1.6 for i in range(n_files)]
    ex = win(d, (60, 70, 520, 930), "Explorer: pentest-agent", fill=CODE_BG)
    T(d, (ex[0] + 20, ex[1] + 26), "pentest-agent/", font(22, True, True), TXT, "lm")
    for i, (name, lvl) in enumerate(FILES):
        if t >= t_i[i]:
            T(d, (ex[0] + 20 + lvl * 24, ex[1] + 66 + i * 38), name, font(21, mono=True),
              AMBER if name.endswith("/") else TXT, "lm")
    cx0, cy0, cx1, cy1 = win(d, (540, 70, 1380, 930), "Editor", fill=CODE_BG)
    marks = [("env", c("environment file", -0.2), c("binds to localhost", -0.2)),
             ("host", c("binds to localhost", -0.2), c("No secrets in code", -0.2)),
             ("git", c("No secrets in code", -0.2), c("I didn't ask", -0.2))]
    active = next((m for m in marks if m[1] <= t < m[2]), None)
    if active:
        name, pill, lines = ZOOMS[active[0]]
        T(d, (cx0 + 24, cy0 + 28), name, font(26, True, True), IBM, "lm")
        d.line((cx0, cy0 + 56, cx1, cy0 + 56), fill=LINE)
        rows = [(s, col, (50, 40, 12) if col == AMBER else None) for s, col in lines]
        code(d, (cx0 + 10, cy0 + 90, cx1 - 10, cy1), rows, fs=24, lh=44)
        callout(d, (cx0 + 24, cy1 - 90), pill, GREEN, t, active[1] + 0.4)
    else:
        T(d, (cx0 + 24, cy0 + 28), "app.py", font(26, True, True), IBM, "lm")
        d.line((cx0, cy0 + 56, cx1, cy0 + 56), fill=LINE)
        stub = [("from flask import Flask, render_template", TXT), ("from core.agent import PentestAgent", TXT),
                ("from core.pentest_guard import PentestGuard", TXT), ("from core.prompt_cache import PromptCache", TXT),
                ("", TXT), ("app = Flask(__name__)", TXT), ("guard = PentestGuard()", TXT), ("cache = PromptCache()", TXT)]
        code(d, (cx0 + 10, cy0 + 90, cx1 - 10, cy1), stub, fs=24, lh=44)
    bx0, by0, bx1, by1 = bob_panel(d, (1400, 70, 1860, 930), "AGENT")
    T(d, (bx0 + 18, by0 + 14), "Plan approved. Scaffolding…", font(22), TXT)
    shown = [f"✓ created {FILES[i][0]}" for i in range(n_files) if t >= t_i[i]][-17:]
    for k, s in enumerate(shown):
        T(d, (bx0 + 18, by0 + 56 + k * 34), s, font(20, mono=True), GREEN if k < len(shown) - 1 else TXT)
    if t < c("I didn't ask", -0.2):
        chip(d, 1100, 20, "ACCELERATED", AMBER, font(20, True), h=40)
    p = prog(t, c("Those are our team's rules"), 0.5)
    if p > 0:
        box(d, (540, 842, 1380, 922), fill=mix(BG, IBM_DARK, 0.9 * p), outline=mix(BG, IBM, p), w=2, rad=12)
        T(d, (960, 868), "Rules came from the team's project rules,", font(22, True), mix(BG, WHITE, p), "mm")
        T(d, (960, 898), "not from the prompt.", font(22, True), mix(BG, WHITE, p), "mm")


TESTS = [("tests/test_config.py", 2), ("tests/test_pentest_guard.py", 5), ("tests/test_prompt_cache.py", 4),
         ("tests/test_hexstrike_tools.py", 2), ("tests/test_agent.py", 2), ("tests/test_reporter.py", 1)]


# Scene 6: validate (tests, app, authorization guard) - Sat 14 Nov 2026 18:10 CET
def s6(img, d, t):
    c = K(6)
    paint_backdrop(img)
    t_test, t_pass, t_start = c("Bob writes the tests"), c("Sixteen passing"), c("starts the app")
    t_guard, t_ok, t_ver = c("The guard catches"), c("until I confirm"), c("verified, not")
    lines = [("$ ./run.sh test", TXT, t_test), ("collected 16 items", MUTED, t_test + 1.2)]
    for k, (name, n) in enumerate(TESTS):
        lines.append((f"{name} {'.' * n}", GREEN, t_test + 1.8 + k * 0.45))
    lines += [("", TXT, t_pass), ("==== 16 passed in 2.31s ====", GREEN, t_pass),
              ("$ ./run.sh start", TXT, t_start), ("[+] config loaded (.env)", MUTED, t_start + 1.4),
              ("[+] SQLite audit ledger ready", MUTED, t_start + 1.9),
              ("[+] Serving on http://127.0.0.1:5000", GREEN, t_start + 2.4)]
    term(d, (60, 70, 940, 930), lines, t, "terminal: pentest-agent", 20, 30)
    if t >= t_pass:
        chip(d, 560, 100, "16 / 16 TESTS PASSING", GREEN, font(24, True), h=52)
    cx0, cy0, cx1, cy1 = chrome(d, "http://127.0.0.1:5000", (980, 70, 1860, 930))
    if t < t_start + 2.4:
        T(d, ((cx0 + cx1) / 2, (cy0 + cy1) / 2), "waiting for server…", font(30), MUTED, "mm")
    else:
        d.rectangle((cx0, cy0, cx1, cy0 + 60), fill=PANEL2)
        T(d, (cx0 + 20, cy0 + 30), "Pentest Agent", font(26, True), TXT, "lm")
        chip(d, cx1 - 200, cy0 + 8, "gpt-4.1-mini", CYAN, font(18, True), h=44)
        for k, nm in enumerate(["Chat", "Audit", "Settings"]):
            sel = k == (1 if t >= t_ver else 0)
            T(d, (cx0 + 300 + k * 90, cy0 + 30), nm, font(20, sel), TXT if sel else MUTED, "lm")
        t_ask = c("I try a scan request")
        if t >= t_ask:
            msg = typed("Run an nmap scan on 10.0.0.0/24.", t - t_ask, 18)
            box(d, (cx0 + 200, cy0 + 110, cx1 - 24, cy0 + 170), fill=mix(BG, IBM_DARK, 0.8), rad=14)
            T(d, (cx0 + 222, cy0 + 140), msg, font(22), WHITE, "lm")
        box(d, (cx0 + 20, cy1 - 76, cx1 - 20, cy1 - 20), fill=PANEL2, outline=LINE, w=2, rad=12)
        T(d, (cx0 + 40, cy1 - 48), "Message Bob…", font(20), MUTED, "lm")
        if t_guard <= t < t_ver:
            ov = Image.new("RGBA", (cx1 - cx0, cy1 - cy0), (0, 0, 0, 150))
            img.paste(ov, (cx0, cy0), ov)
            d = ImageDraw.Draw(img)
            mx0, my0 = cx0 + 40, cy0 + 150
            box(d, (mx0, my0, cx1 - 40, my0 + 380), fill=PANEL, outline=RED, w=3, rad=16)
            T(d, (mx0 + 28, my0 + 44), "Authorization Required", font(32, True), TXT, "lm")
            for j, ln in enumerate(wrap("Scanning intent detected for 10.0.0.0/24. Confirm you are permitted to test this target.",
                                         font(22), 680)):
                T(d, (mx0 + 28, my0 + 100 + j * 30), ln, font(22), MUTED, "lm")
            okp = t >= t_ok
            check(d, mx0 + 28, my0 + 200, "I am authorised to test this scope", done=okp, col=GREEN, f=font(22))
            chip(d, mx0 + 28, my0 + 280, "AUTHORIZED" if okp else "BLOCKED UNTIL AUTHORIZED",
                 GREEN if okp else RED, font(22, True), h=48)
        if t >= t_ver:
            box(d, (cx0 + 20, cy0 + 200, cx1 - 20, cy0 + 460), fill=GH_BG, outline=GREEN, w=2, rad=12)
            T(d, (cx0 + 40, cy0 + 232), "AUDIT LOG", font(18, True), MUTED, "lm")
            T(d, (cx0 + 40, cy0 + 280), "prompt: Run an nmap scan on 10.0.0.0/24", font(19, mono=True), TXT, "lm")
            T(d, (cx0 + 40, cy0 + 320), "target: 10.0.0.0/24   risk: high", font(19, mono=True), TXT, "lm")
            T(d, (cx0 + 40, cy0 + 360), "consent: confirmed by operator  ✓", font(19, mono=True), GREEN, "lm")
    p = prog(t, c("We went from"), 0.5)
    if p > 0:
        box(d, (360, 868, 1560, 936), fill=mix(BG, IBM_DARK, 0.9 * p), outline=mix(BG, IBM, p), w=2, rad=34)
        T(d, (960, 902), "EMPTY FOLDER   →   WORKING, TESTED APP", font(32, True), mix(BG, WHITE, p), "mm")
