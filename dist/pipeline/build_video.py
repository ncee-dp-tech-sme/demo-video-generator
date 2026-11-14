# Video stage: renders every frame with Pillow (parallel), pipes raw frames into ffmpeg,
# muxes build/audio.wav and writes output/HexStrike_demo.mp4 plus captions .srt.
# Usage:
#   python build_video.py render            # full video
#   python build_video.py still <sec> [png] # single preview frame
#
# Change log
# Sat 14 Nov 2026 17:45 CET - Initial version: 9 scenes following HexStrike_AV_script_v1.md.

import math
import random
import subprocess
import sys
from functools import lru_cache
from multiprocessing import Pool, cpu_count

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

import demo_common as C
from build_audio import LOCK_CUE

W, H, FPS = C.W, C.H, C.FPS
BG = (9, 13, 19); PANEL = (17, 24, 33); PANEL2 = (26, 36, 50); LINE = (44, 58, 76)
TXT = (226, 232, 240); MUTED = (125, 140, 160); CYAN = (34, 211, 238); GREEN = (34, 197, 94)
RED = (239, 68, 68); AMBER = (245, 158, 11); BLUE = (59, 130, 246); PURPLE = (168, 85, 247)
BLACK = (0, 0, 0); WHITE = (255, 255, 255)
BICUBIC = Image.Resampling.BICUBIC
CAPS = []


# ---------------------------------------------------------------- helpers

# Cached font loader (sans = Helvetica Neue, mono = Menlo) - Sat 14 Nov 2026 17:45 CET
@lru_cache(maxsize=None)
def font(size, bold=False, mono=False):
    path = "/System/Library/Fonts/Menlo.ttc" if mono else "/System/Library/Fonts/HelveticaNeue.ttc"
    return ImageFont.truetype(path, size, index=1 if bold else 0)


# Clamp a number to a range - Sat 14 Nov 2026 17:45 CET
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


# Smoothstep easing - Sat 14 Nov 2026 17:45 CET
def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


# Linear colour mix - Sat 14 Nov 2026 17:45 CET
def mix(a, b, t):
    t = clamp(t)
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# Draw text with anchor - Sat 14 Nov 2026 17:45 CET
def T(d, xy, s, f, fill=TXT, anchor="la"):
    d.text(xy, s, font=f, fill=fill, anchor=anchor)


# Rounded rectangle shortcut - Sat 14 Nov 2026 17:45 CET
def box(d, r, fill=None, outline=None, w=2, rad=14):
    d.rounded_rectangle([int(v) for v in r], rad, fill=fill, outline=outline, width=w)


# Typewriter text at chars-per-second - Sat 14 Nov 2026 17:45 CET
def typed(s, t, cps=30):
    return s[: max(0, int(t * cps))]


# Blink helper - Sat 14 Nov 2026 17:45 CET
def blink(t, rate=1.0):
    return int(t * 2 * rate) % 2 == 0


# Glowing dot (status light) - Sat 14 Nov 2026 17:45 CET
def light(d, c, r, col, bg, k=1.0):
    for i in range(6, 0, -1):
        d.ellipse((c[0] - r - i * 5, c[1] - r - i * 5, c[0] + r + i * 5, c[1] + r + i * 5),
                  fill=mix(bg, col, 0.03 * k * (7 - i)))
    d.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), fill=mix(bg, col, 0.35 + 0.65 * k))


# Rotated bordered label stamp - Sat 14 Nov 2026 17:45 CET
def stamp(img, text, center, angle, col, size=64):
    f = font(size, True)
    w, h = int(f.getlength(text)) + 60, size + 40
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle((0, 0, w - 1, h - 1), 12, fill=(16, 8, 10, 235), outline=col + (255,), width=6)
    ld.text((w / 2, h / 2), text, font=f, fill=col + (255,), anchor="mm")
    layer = layer.rotate(angle, expand=True, resample=BICUBIC)
    img.paste(layer, (int(center[0] - layer.width / 2), int(center[1] - layer.height / 2)), layer)


# Subtle background grid - Sat 14 Nov 2026 17:45 CET
def grid(d, col=(14, 20, 29), step=60):
    for x in range(0, W, step):
        d.line((x, 0, x, H), fill=col)
    for y in range(0, H, step):
        d.line((0, y, W, y), fill=col)


# Browser window chrome; returns content rect - Sat 14 Nov 2026 17:45 CET
def chrome(d, url, rect=(120, 60, 1800, 940)):
    x0, y0, x1, y1 = rect
    box(d, rect, fill=PANEL, outline=LINE, w=2, rad=18)
    d.rounded_rectangle((x0, y0, x1, y0 + 56), 18, fill=(30, 40, 54))
    d.rectangle((x0, y0 + 30, x1, y0 + 56), fill=(30, 40, 54))
    for i, c in enumerate([RED, AMBER, GREEN]):
        d.ellipse((x0 + 22 + i * 28, y0 + 20, x0 + 38 + i * 28, y0 + 36), fill=c)
    box(d, (x0 + 140, y0 + 10, x1 - 140, y0 + 46), fill=BG, rad=18)
    T(d, (x0 + 170, y0 + 28), url, font(22, mono=True), MUTED, "lm")
    return (x0, y0 + 56, x1, y1)


# Draw a chip and return its right edge - Sat 14 Nov 2026 17:45 CET
def chip(d, x, y, s, col, f=None, h=48, fill=None):
    f = f or font(24, True)
    w = int(f.getlength(s)) + 40
    box(d, (x, y, x + w, y + h), fill=fill or mix(PANEL, col, 0.18), outline=col, w=2, rad=h // 2)
    T(d, (x + w / 2, y + h / 2), s, f, col, "mm")
    return x + w


# ---------------------------------------------------------------- scene 1: boot + messy desk

BOOT = ["HEXSTRIKE-AV secure boot v5.1", "[ OK ] memory check", "[ OK ] mounting /dev/engagements",
        "[ OK ] loading tool registry ... 150+ tools", "[ OK ] PentestGuard armed", "[ .. ] awaiting operator"]


# Deterministic fake nmap output line - Sat 14 Nov 2026 17:45 CET
def nmap_line(k):
    if k % 9 == 0:
        return f"Nmap scan report for 10.20.0.{(k // 9) % 250 + 2}", AMBER
    svc = [("22/tcp", "ssh"), ("53/tcp", "domain"), ("80/tcp", "http"), ("443/tcp", "https"), ("445/tcp", "smb"),
           ("3306/tcp", "mysql"), ("8080/tcp", "http-proxy"), ("5432/tcp", "postgresql"), ("6379/tcp", "redis")]
    p, s = svc[(k * 7 + k // 9) % len(svc)]
    return f"{p:<10}open  {s}", (130, 230, 150)


# Messy desk scene - Sat 14 Nov 2026 17:45 CET
def desk(img, d, t):
    d.rectangle((0, 0, W, H), fill=(20, 22, 28))
    d.rectangle((0, 780, W, H), fill=(58, 40, 29))
    for y in range(800, H, 40):
        d.line((0, y, W, y), fill=(48, 33, 24), width=2)
    # monitor
    box(d, (120, 40, 1280, 790), fill=(12, 14, 18), outline=(55, 60, 70), w=4, rad=22)
    d.rectangle((640, 790, 760, 840), fill=(30, 33, 40))
    d.rectangle((560, 835, 840, 855), fill=(30, 33, 40))
    d.rectangle((150, 70, 1250, 760), fill=(236, 238, 243))
    # tab strip: 40 tabs
    d.rectangle((150, 70, 1250, 116), fill=(196, 202, 213))
    r = random.Random(7)
    for i in range(40):
        x = 152 + i * 27
        col = (255, 255, 255) if i == 39 else mix((205, 210, 220), (170, 178, 195), r.random())
        d.rounded_rectangle((x, 78, x + 25, 116), 5, fill=col)
        d.rectangle((x + 8, 92, x + 16, 100), fill=r.choice([RED, BLUE, AMBER, GREEN, PURPLE]))
    d.rectangle((150, 116, 1250, 150), fill=(255, 255, 255))
    T(d, (166, 133), "nvd.nist.gov/vuln/detail/CVE-2024-...", font(18, mono=True), (90, 95, 105), "lm")
    # page text (writeup)
    off = int(t * 6) % 20
    r = random.Random(3)
    y = 170 - off
    for k in range(26):
        wdt = r.randint(180, 430)
        if k % 7 == 0:
            d.rectangle((170, y, 170 + 300, y + 18), fill=(60, 66, 80))
            y += 36
        else:
            d.rectangle((170, y, 170 + wdt, y + 12), fill=(176, 182, 194))
            y += 24
        if y > 740:
            break
    # terminal with scrolling nmap
    box(d, (600, 190, 1230, 740), fill=(8, 10, 14), outline=(70, 76, 90), w=2, rad=8)
    d.rectangle((600, 190, 1230, 222), fill=(36, 40, 50))
    T(d, (616, 206), "nmap -sV -sC -p- 10.20.0.0/24", font(16, mono=True), MUTED, "lm")
    top = int(t * 12)
    for row in range(20):
        txt, col = nmap_line(top + row)
        T(d, (620, 238 + row * 24), txt, font(17, mono=True), col)
    # sticky notes
    for (x, y, s, col) in [(1310, 50, "retest?", (250, 224, 120)), (1420, 80, "scope??", (250, 170, 190)),
                           (1530, 45, "call client", (160, 220, 250))]:
        d.rectangle((x, y, x + 100, y + 100), fill=col)
        T(d, (x + 50, y + 50), s, font(19, True), (60, 50, 30), "mm")
    # draft CVE report (rotated paper)
    paper = Image.new("RGBA", (400, 600), (0, 0, 0, 0))
    pd = ImageDraw.Draw(paper)
    pd.rectangle((0, 0, 399, 599), fill=(250, 250, 247), outline=(200, 200, 195))
    pd.text((24, 28), "CVE REPORT - DRAFT", font=font(26, True), fill=(40, 40, 50))
    pd.text((24, 70), "Finding 1: ???", font=font(20, mono=True), fill=(80, 80, 90))
    for k, wd in enumerate([340, 300, 330, 250, 320, 180]):
        pd.rectangle((24, 120 + k * 28, 24 + wd, 130 + k * 28), fill=(205, 205, 200))
    pd.text((24, 330), "CVSS: ?   CWE: ?", font=font(20, mono=True), fill=(190, 60, 60))
    pd.text((24, 380), "Remediation: TODO" + ("_" if blink(t) else ""), font=font(20, mono=True), fill=(80, 80, 90))
    pd.text((24, 540), "...", font=font(30, True), fill=(120, 120, 120))
    paper = paper.rotate(4, expand=True, resample=BICUBIC)
    img.paste(paper, (1340, 190), paper)
    # keyboard, mouse, mug, steam, paper pile
    d.rounded_rectangle((250, 880, 1000, 990), 10, fill=(30, 33, 40), outline=(50, 54, 64))
    for rr in range(4):
        for cc in range(22):
            d.rectangle((266 + cc * 33, 892 + rr * 24, 290 + cc * 33, 908 + rr * 24), fill=(48, 52, 62))
    d.ellipse((1080, 900, 1130, 970), fill=(40, 44, 54))
    d.rounded_rectangle((1250, 850, 1350, 960), 12, fill=(220, 220, 225))
    d.arc((1330, 875, 1390, 935), 270, 90, fill=(220, 220, 225), width=10)
    for k in range(3):
        sx = 1280 + k * 25
        pts = [(sx + math.sin(t * 2 + k + j * 0.6) * 8, 840 - j * 14) for j in range(7)]
        d.line(pts, fill=(150, 150, 160), width=3)
    d.rectangle((1470, 830, 1820, 960), fill=(215, 215, 208), outline=(170, 170, 165))
    d.rectangle((1500, 810, 1850, 940), fill=(228, 228, 222), outline=(170, 170, 165))
    T(d, (1520, 830), "scan_final_v3_REAL.txt", font(16, mono=True), (90, 90, 95))


# Scene 1 - Sat 14 Nov 2026 17:45 CET
def scene1(img, d, t):
    if t < 3.4:
        d.rectangle((0, 0, W, H), fill=BLACK)
        y = 120
        for i, line in enumerate(BOOT):
            if t > 0.3 + i * 0.45:
                T(d, (120, y), line, font(34, mono=True), GREEN if "OK" in line else TXT)
                y += 54
        if blink(t):
            d.rectangle((120, y + 4, 150, y + 40), fill=GREEN)
    else:
        desk(img, d, t - 3.4)
        if t < 3.55:
            d.rectangle((0, 0, W, H), fill=mix(BG, WHITE, 0.15))


# ---------------------------------------------------------------- scene 2: dashboard + Bob persona

PLAN = ["Scope + rules of engagement", "Passive recon", "Service enumeration", "Vulnerability analysis",
        "Exploitation (authorization gate)", "Report + remediation"]


# Scene 2 - Sat 14 Nov 2026 17:45 CET
def scene2(img, d, t):
    cx0, cy0, cx1, cy1 = chrome(d, "http://127.0.0.1:5000", (120, 60, 1800, 940))
    if t < 1.8:
        T(d, (960, 480), "Loading HexStrike...", font(40, True), TXT, "mm")
        box(d, (710, 540, 1210, 556), fill=PANEL2, rad=8)
        box(d, (710, 540, 710 + 500 * ease(t / 1.6) + 12, 556), fill=CYAN, rad=8)
        return
    d.rectangle((cx0 + 2, cy0, 360, cy1 - 2), fill=(13, 19, 27))
    T(d, (150, 150), "HEXSTRIKE", font(30, True), CYAN)
    for k, s in enumerate(["Dashboard", "Engagements", "Tools", "Reports", "Audit log"]):
        if k == 0:
            box(d, (140, 215, 340, 262), fill=mix(PANEL, CYAN, 0.15), rad=10)
        T(d, (160, 238 + k * 56), s, font(24), TXT if k == 0 else MUTED, "lm")
    T(d, (400, 150), "HexStrike Pentest Agent", font(40, True))
    chip(d, 1450, 148, "127.0.0.1 - local only", GREEN, font(20, True), 42)
    tb = cue_(1, "call him Bob")
    a = ease((t - tb) / 0.6)
    box(d, (400, 230, 1100, 700), fill=PANEL2 if t >= tb else PANEL, outline=LINE, w=2, rad=18)
    if t >= tb:
        yo = int((1 - a) * 30)
        T(d, (440, 262 + yo), "AGENT PERSONA", font(20, mono=True), mix(PANEL2, MUTED, a))
        T(d, (436, 290 + yo), "Bob", font(130, True), mix(PANEL2, WHITE, a))
        pulse = 0.75 + 0.25 * math.sin(t * 4)
        light(d, (456, 486), 12, GREEN, PANEL2, pulse)
        T(d, (490, 486), "ACTIVE - planning engagement", font(24, mono=True), mix(PANEL2, GREEN, a), "lm")
        x, y = 440, 540
        for phrase, label in [("OWASP methodology", "OWASP methodology"), ("API abuse chains", "API abuse chains"),
                              ("infrastructure recon", "Infrastructure recon"), ("exploitation logic", "Exploitation logic")]:
            if t >= cue_(1, phrase):
                wch = int(font(24, True).getlength(label)) + 40
                if x + wch > 1070:
                    x, y = 440, y + 62
                x = chip(d, x, y, label, CYAN) + 14
    box(d, (1130, 230, 1770, 700), fill=PANEL, outline=LINE, w=2, rad=18)
    T(d, (1160, 262), "Engagement plan", font(32, True))
    tp = cue_(1, "plans the engagement")
    for k, s in enumerate(PLAN):
        if t >= tp + k * 0.55:
            col = AMBER if "gate" in s else TXT
            T(d, (1160, 330 + k * 56), f"{k + 1:02d}", font(24, True, True), CYAN)
            T(d, (1215, 330 + k * 56), s, font(23), col)
    box(d, (400, 730, 1770, 910), fill=(6, 9, 13), outline=LINE, w=2, rad=14)
    lines = ["> loading methodology: OWASP WSTG + API Security Top 10",
             "> plan: recon -> enumerate -> analyse -> [auth gate] -> exploit -> report",
             "> packets sent: 0"]
    y = 760
    for k, s in enumerate(lines):
        T(d, (430, y), typed(s, t - tp - k * 1.4, 45), font(24, mono=True), GREEN if k < 2 else AMBER)
        y += 44


# ---------------------------------------------------------------- scene 3: architecture

# Scene 3 - Sat 14 Nov 2026 17:45 CET
def scene3(img, d, t):
    grid(d)
    T(d, (960, 120), "Architecture", font(54, True), TXT, "mm")
    T(d, (960, 175), "persona  >  MCP server  >  model backend", font(24, mono=True), MUTED, "mm")
    nodes = [(100, "Bob", "senior-pentester persona", CYAN, "Bob doesn't"),
             (740, "HexStrike AI MCP Server", "tool orchestration layer", PURPLE, "HexStrike AI MCP Server"),
             (1380, "1min.AI", "OpenAI-compatible API", GREEN, "1min.AI")]
    for x, name, sub, col, ph in nodes:
        tc = cue_(2, ph)
        if t < tc:
            continue
        a = ease((t - tc) / 0.5)
        yo = int((1 - a) * 40)
        box(d, (x, 360 + yo, x + 440, 600 + yo), fill=mix(BG, mix(PANEL, col, 0.14), a), outline=mix(BG, col, a), w=3, rad=22)
        T(d, (x + 220, 440 + yo), name, font(34 if len(name) > 10 else 52, True), mix(BG, WHITE, a), "mm")
        T(d, (x + 220, 520 + yo), sub, font(24, mono=True), mix(BG, col, a), "mm")
    for (x0, x1, ph, lab) in [(540, 740, "HexStrike AI MCP Server", "MCP"), (1180, 1380, "1min.AI", "/v1/chat")]:
        tc = cue_(2, ph) + 0.3
        if t < tc:
            continue
        y = 480
        d.line((x0 + 10, y, x1 - 24, y), fill=CYAN, width=4)
        d.polygon([(x1 - 10, y), (x1 - 34, y - 14), (x1 - 34, y + 14)], fill=CYAN)
        T(d, ((x0 + x1) / 2, y - 30), lab, font(22, mono=True), MUTED, "mm")
        for k in range(3):
            p = ((t - tc) * 0.7 + k / 3) % 1
            px = x0 + 10 + (x1 - x0 - 40) * p
            d.ellipse((px - 7, y - 7, px + 7, y + 7), fill=WHITE)
    x = 180
    for ph, lab, col in [("Free account", "Free account", GREEN), ("real reasoning", "Real reasoning", CYAN),
                         ("zero API key", "Zero API key juggling", AMBER)]:
        if t >= cue_(2, ph):
            x = chip(d, x, 720, lab, col, font(30, True), 64) + 24


# ---------------------------------------------------------------- scene 4: orchestra

TOOLS = [("Nmap", "RECON", CYAN, "Nmap and Masscan", 0), ("Masscan", "RECON", CYAN, "Nmap and Masscan", 0.9),
         ("Nuclei", "VULN SWEEP", AMBER, "Nuclei and Nikto", 0), ("Nikto", "VULN SWEEP", AMBER, "Nuclei and Nikto", 0.9),
         ("Gobuster", "DISCOVERY", GREEN, "Gobuster and FFUF", 0), ("FFUF", "DISCOVERY", GREEN, "Gobuster and FFUF", 0.9),
         ("SQLMap", "INJECTION", RED, "SQLMap for injection", 0), ("Hydra", "CREDENTIALS", PURPLE, "Hydra for", 0),
         ("Trivy", "CONTAINERS", BLUE, "Trivy for", 0)]


# Tile centre on the orchestra arc - Sat 14 Nov 2026 17:45 CET
def arc_pos(k, n=9):
    phi = math.pi * (0.06 + 0.88 * k / (n - 1))
    return (960 - 700 * math.cos(phi), 800 - 440 * math.sin(phi))


# Scene 4 - Sat 14 Nov 2026 17:45 CET
def scene4(img, d, t):
    grid(d)
    t_over = cue_(3, "Over a hundred fifty")
    if t < t_over:
        T(d, (960, 100), "The orchestra", font(52, True), TXT, "mm")
    else:
        T(d, (960, 100), "150+ tools", font(60, True), CYAN, "mm")
        T(d, (960, 156), "Bob picks the next move", font(26, mono=True), MUTED, "mm")
    lit_times = [cue_(3, ph) + off for (_, _, _, ph, off) in TOOLS]
    active = None
    for k, tt in enumerate(lit_times):
        if t >= tt and (active is None or tt >= lit_times[active]):
            active = k
    for k, (name, cat, col, ph, off) in enumerate(TOOLS):
        x, y = arc_pos(k)
        lit = t - lit_times[k]
        if lit >= 0:
            pulse = clamp(1 - lit / 1.4)
            fill = mix(PANEL, col, 0.16 + 0.22 * pulse)
            outline = mix(col, WHITE, 0.5 * pulse)
            w = 4
        else:
            fill, outline, w = PANEL, LINE, 2
        box(d, (x - 110, y - 58, x + 110, y + 58), fill=fill, outline=outline, w=w, rad=18)
        cc = col if lit >= 0 else MUTED
        d.ellipse((x - 94, y - 24, x - 46, y + 24), outline=cc, width=3)
        T(d, (x - 70, y), name[0], font(28, True), cc, "mm")
        T(d, (x - 34, y - 12), name, font(28, True), TXT if lit >= 0 else MUTED, "lm")
        T(d, (x - 34, y + 22), cat, font(15, mono=True), cc, "lm")
    # conductor on podium
    d.polygon([(830, 940), (1090, 940), (1040, 860), (880, 860)], fill=(40, 50, 66), outline=LINE)
    box(d, (922, 730, 998, 860), fill=PANEL2, outline=CYAN, w=3, rad=16)
    d.ellipse((926, 650, 994, 718), fill=PANEL2, outline=CYAN, width=3)
    T(d, (960, 795), "Bob", font(22, True), CYAN, "mm")
    hand = (1030, 745)
    d.line((998, 760, hand[0], hand[1]), fill=CYAN, width=8)
    tx, ty = arc_pos(active) if active is not None else (960, 400)
    ang = math.atan2(ty - hand[1], tx - hand[0]) + math.sin(t * 9) * 0.22
    d.line((hand[0], hand[1], hand[0] + 150 * math.cos(ang), hand[1] + 150 * math.sin(ang)), fill=WHITE, width=5)
    d.line((922, 760, 880, 800), fill=CYAN, width=8)
    if t >= cue_(3, "not a script"):
        s = "for tool in tools: run()"
        T(d, (180, 880), s, font(26, mono=True), MUTED)
        wd = font(26, mono=True).getlength(s)
        d.line((170, 893, 190 + wd, 893), fill=RED, width=4)
        T(d, (180, 920), "not a script running top to bottom", font(20, mono=True), RED)


# ---------------------------------------------------------------- scene 5: blocked

# Scene 5 - Sat 14 Nov 2026 17:45 CET
def scene5(img, d, t):
    d.rectangle((0, 0, W, H), fill=(16, 8, 10))
    a = ease(t / 0.4)
    yo = int(-(1 - a) * 160)
    flash = 0.75 + 0.25 * (math.sin(t * 8) if t < 6 else 1)
    d.rectangle((0, 40 + yo, W, 170 + yo), fill=mix((60, 10, 12), RED, flash))
    for x in range(-100, W, 70):
        d.polygon([(x, 40 + yo), (x + 35, 40 + yo), (x - 15, 54 + yo), (x - 50, 54 + yo)], fill=(30, 5, 6))
    T(d, (960, 105 + yo), "SCAN BLOCKED", font(100, True), WHITE, "mm")
    if t >= cue_(4, "PentestGuard"):
        chip(d, 560, 188, "PentestGuard: scanning intent detected - HIGH RISK", AMBER, font(24, True), 46)
    box(d, (480, 262, 1440, 930), fill=PANEL, outline=RED, w=3, rad=22)
    T(d, (520, 292), "Authorization Required", font(50, True))
    T(d, (520, 358), "Upload signed scope to continue.", font(26, mono=True), MUTED)
    for lab, ph, y in [("Client name", "e.g. Acme Corp", 410), ("Target range", "10.0.0.0/24", 520)]:
        T(d, (520, y), lab, font(22, True), MUTED)
        box(d, (520, y + 30, 1400, y + 82), fill=(10, 14, 20), outline=RED if blink(t, 0.5) else mix(RED, LINE, 0.5), w=2, rad=10)
        T(d, (540, y + 56), ph, font(24, mono=True), (70, 82, 98), "lm")
        T(d, (1380, y + 56), "required", font(18, mono=True), RED, "rm")
    T(d, (520, 630), "Signature", font(22, True), MUTED)
    for x in range(520, 1400, 26):
        d.line((x, 662, x + 14, 662), fill=RED, width=2)
        d.line((x, 770, x + 14, 770), fill=RED, width=2)
    d.line((520, 662, 520, 770), fill=RED, width=2)
    d.line((1400, 662, 1400, 770), fill=RED, width=2)
    T(d, (960, 716), "Drop signed scope document here (PDF / .sig)", font(24, mono=True), (90, 102, 118), "mm")
    box(d, (520, 810, 1400, 886), fill=(34, 40, 50), outline=LINE, rad=14)
    T(d, (960, 848), "Submit scope  (disabled)", font(28, True), (90, 100, 115), "mm")
    if t >= cue_(4, "No signed authorization"):
        stamp(img, "NO SIGNATURE, NO SCAN", (960, 600), 7, RED, 66)
    if t >= cue_(4, "difference between"):
        box(d, (40, 520, 440, 700), fill=mix(PANEL, GREEN, 0.15), outline=GREEN, w=3, rad=18)
        T(d, (240, 580), "PENTEST", font(44, True), GREEN, "mm")
        T(d, (240, 640), "signed scope", font(24, mono=True), GREEN, "mm")
        box(d, (1480, 520, 1880, 700), fill=mix(PANEL, RED, 0.15), outline=RED, w=3, rad=18)
        T(d, (1680, 580), "FELONY", font(44, True), RED, "mm")
        T(d, (1680, 640), "no signature", font(24, mono=True), RED, "mm")


# ---------------------------------------------------------------- scene 6: caps + lock

# Scene 6 - Sat 14 Nov 2026 17:45 CET
def scene6(img, d, t):
    grid(d)
    t1, t2 = cue_(5, "Payloads capped"), cue_(5, "tool calls capped")
    t3 = cue_(5, LOCK_CUE[1])
    box(d, (160, 170, 900, 540), fill=PANEL, outline=CYAN, w=3, rad=22)
    T(d, (200, 210), "PAYLOAD CAP", font(22, mono=True), MUTED)
    T(d, (200, 250), "100,000", font(120, True, True), CYAN)
    T(d, (200, 400), "characters per payload", font(26, mono=True), MUTED)
    box(d, (200, 460, 860, 490), fill=PANEL2, rad=10)
    f1 = ease((t - t1) / 1.6)
    box(d, (200, 460, 200 + 660 * f1 + 12, 490), fill=CYAN if f1 < 1 else RED, rad=10)
    box(d, (1020, 170, 1760, 540), fill=PANEL, outline=AMBER, w=3, rad=22)
    T(d, (1060, 210), "TOOL-CALL CAP", font(22, mono=True), MUTED)
    T(d, (1060, 250), "128", font(120, True, True), AMBER)
    T(d, (1060, 400), "tool calls per run", font(26, mono=True), MUTED)
    n = int(128 * ease((t - t2) / 1.8))
    for k in range(128):
        x, y = 1060 + (k % 64) * 10, 450 + (k // 64) * 20
        d.rectangle((x, y, x + 7, y + 14), fill=AMBER if k < n else PANEL2)
    # padlock: shackle lifted until the guardrails cue, then snaps shut
    closed = t >= t3
    lift = 46
    if closed:
        snap = clamp((t - t3) / 0.18)
        lift = -int(8 * math.sin(snap * math.pi)) if snap < 1 else 0
    col = GREEN if closed else MUTED
    d.arc((900, 640 - lift - 10, 1020, 770 - lift), 180, 360, fill=col, width=22)
    d.line((910, 705 - lift, 910, 760), fill=col, width=22)
    d.line((1010, 705 - lift, 1010, 760), fill=col, width=22)
    box(d, (870, 750, 1050, 890), fill=mix(PANEL, col, 0.35), outline=col, w=4, rad=18)
    d.ellipse((945, 800, 975, 830), fill=BG)
    d.rectangle((954, 820, 966, 860), fill=BG)
    if closed:
        ring = clamp((t - t3) / 0.8)
        r = 110 + 90 * ring
        d.ellipse((960 - r, 820 - r, 960 + r, 820 + r), outline=mix(GREEN, BG, ring), width=4)
        T(d, (960, 935), "Guardrails on the guardrails", font(34, True, True), GREEN, "mm")


# ---------------------------------------------------------------- scene 7: ledger + report

PROMPTS = ["enumerate subdomains for scope", "run service scan on 10.20.0.0/24", "nuclei sweep: web tier",
           "directory discovery on /api", "test login form for injection", "credential audit: ssh hosts",
           "scan container images", "exploit confirmed SQLi on /orders", "full port scan, external range",
           "brute-force admin portal"]
TARGETS = ["acme-corp.example", "10.20.0.0/24", "app.acme-corp.example", "api.acme-corp.example",
           "10.20.0.14", "10.20.0.31", "registry.acme-corp.example", "10.20.0.0/24"]


# Scene 7 - Sat 14 Nov 2026 17:45 CET
def scene7(img, d, t):
    tcut = cue_(6, "When the engagement closes")
    if t < tcut:
        grid(d)
        T(d, (200, 100), "ledger.db", font(40, True, True), CYAN)
        T(d, (200, 150), "SQLite audit trail", font(24, mono=True), MUTED)
        box(d, (200, 200, 1720, 930), fill=PANEL, outline=LINE, w=2, rad=16)
        d.rectangle((202, 202, 1718, 262), fill=PANEL2)
        cols = [(230, "timestamp"), (590, "prompt"), (1190, "target"), (1550, "consent")]
        for x, s in cols:
            T(d, (x, 232), s, font(24, True, True), CYAN, "lm")
        s = t * 80
        first, frac = int(s // 64), s % 64
        for r in range(12):
            k = first + r
            y = 262 + r * 64 - frac
            if y < 262 or y > 866:
                continue
            ok = k % 5 != 3
            ts = f"2026-11-14 09:{(k * 3) // 60 % 60:02d}:{(k * 3 + 11) % 60:02d}"
            if not ok:
                d.rectangle((204, y, 1716, y + 62), fill=mix(PANEL, RED, 0.18))
            row = [ts, PROMPTS[k % len(PROMPTS)], TARGETS[(k * 3) % len(TARGETS)], "TRUE" if ok else "FALSE"]
            for (x, _), v in zip(cols, row):
                col = GREEN if v == "TRUE" else RED if v == "FALSE" else TXT
                T(d, (x, y + 32), v, font(22, mono=True), col, "lm")
            d.line((204, y + 63, 1716, y + 63), fill=LINE)
        return
    # report view
    d.rectangle((0, 0, W, H), fill=(14, 18, 25))
    box(d, (110, 190, 600, 790), fill=(8, 11, 16), outline=LINE, w=2, rad=10)
    T(d, (134, 214), "report.md", font(22, True, True), MUTED)
    md = ["# Finding F-001", "", "**Title:** SQL injection", "**Endpoint:** /api/v2/orders", "**CVSS v3.1:** 9.8", "**CWE:** CWE-89", "",
          "## Remediation", "1. Parameterised queries", "2. Input allow-lists", "3. Least-privilege DB user"]
    for k, s in enumerate(md):
        T(d, (134, 262 + k * 40), s, font(20, mono=True), CYAN if s.startswith("#") else TXT)
    px0, py0, px1, py1 = 660, 40, 1300, 945
    d.rectangle((px0 + 8, py0 + 8, px1 + 8, py1 + 8), fill=(5, 7, 10))
    d.rectangle((px0, py0, px1, py1), fill=(252, 252, 250))
    ink, grey = (30, 35, 45), (200, 204, 212)
    T(d, (px0 + 40, py0 + 40), "Penetration Test Report", font(34, True), ink)
    T(d, (px0 + 40, py0 + 90), "Client: Acme Corp   |   Engagement 2026-Q4", font(18, mono=True), (100, 105, 115))
    d.line((px0 + 40, py0 + 125, px1 - 40, py0 + 125), fill=grey, width=3)
    T(d, (px0 + 40, py0 + 150), "F-001  SQL injection in /api/v2/orders", font(26, True), ink)
    t_cvss, t_cwe, t_rem = cue_(6, "CVSS v3.1 scored"), cue_(6, "CWE referenced"), cue_(6, "line by line")
    if t >= t_cvss:
        box(d, (px0 + 40, py0 + 205, px0 + 250, py0 + 285), fill=(200, 40, 40), rad=10)
        T(d, (px0 + 145, py0 + 245), "9.8 CRITICAL", font(26, True), WHITE, "mm")
        T(d, (px0 + 270, py0 + 218), "CVSS v3.1", font(22, True), ink)
        T(d, (px0 + 270, py0 + 250), "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", font(13, mono=True), (100, 105, 115))
    if t >= t_cwe:
        T(d, (px0 + 40, py0 + 320), "CWE-89", font(26, True, True), (30, 90, 190))
        T(d, (px0 + 40, py0 + 358), "Improper neutralisation of special elements", font(16), (100, 105, 115))
        T(d, (px0 + 40, py0 + 380), "used in an SQL command", font(16), (100, 105, 115))
    for k, wd in enumerate([520, 480, 500, 300]):
        d.rectangle((px0 + 40, py0 + 430 + k * 24, px0 + 40 + wd, py0 + 442 + k * 24), fill=grey)
    if t >= t_rem:
        T(d, (px0 + 40, py0 + 560), "Remediation", font(26, True), ink)
        for k, s in enumerate(["1. Use parameterised queries", "2. Validate input with allow-lists",
                               "3. Run DB as least-privilege user", "4. Add WAF rule and regression test"]):
            if t >= t_rem + k * 0.45:
                T(d, (px0 + 40, py0 + 610 + k * 40), s, font(20), ink)
    for (y, lab, tt, col) in [(250, "CVSS v3.1 scored", t_cvss, (220, 60, 60)), (380, "CWE referenced", t_cwe, BLUE),
                              (700, "Remediation, line by line", t_rem, GREEN)]:
        if t >= tt:
            d.line((1304, y, 1345, y), fill=col, width=4)
            chip(d, 1350, y - 26, lab, col, font(22, True), 52)
    T(d, (1350, 130), "report.pdf  -  styled", font(24, mono=True), MUTED)


# ---------------------------------------------------------------- scene 8: run.sh

CMDS = [("./run.sh start", ["[+] Python 3.10 ........... ok", "[+] Container runtime: podman", "[+] SQLite ledger ......... ready",
                            "[+] MCP server listening on http://127.0.0.1:5000", "[+] Bob: online"]),
        ("./run.sh test", ["tests/test_pentestguard ..... PASSED", "tests/test_ledger ........... PASSED",
                           "tests/test_report ........... PASSED", "all checks green"]),
        ("./run.sh backup", ["[+] snapshotting ledger + config", "[+] backup written: backups/hexstrike.tar.gz",
                             "[+] rollback point created"])]


# Scene 8 - Sat 14 Nov 2026 17:45 CET
def scene8(img, d, t):
    grid(d)
    starts = [cue_(7, "one run.sh"), cue_(7, "test it"), cue_(7, "back it up")]
    box(d, (160, 70, 1760, 600), fill=(6, 9, 13), outline=LINE, w=2, rad=14)
    d.rectangle((162, 72, 1758, 112), fill=PANEL2)
    T(d, (186, 92), "bash - hexstrike", font(20, mono=True), MUTED, "lm")
    cur = -1
    for k, s0 in enumerate(starts):
        if t >= s0:
            cur = k
    if cur < 0:
        T(d, (190, 150), "$ " + ("_" if blink(t) else ""), font(30, mono=True), GREEN)
    else:
        cmd, out = CMDS[cur]
        lt = t - starts[cur]
        T(d, (190, 150), "$ " + typed(cmd, lt, 22), font(30, mono=True), GREEN)
        for k, line in enumerate(out):
            if lt > 1.0 + k * 0.45:
                T(d, (190, 210 + k * 46), line, font(26, mono=True), GREEN if "PASSED" in line else TXT)
    if t >= cue_(7, "roll it back"):
        T(d, (1730, 570), "./run.sh rollback", font(22, mono=True), AMBER, "rm")
    x = 160
    for ph, lab, col in [("Runs local", "127.0.0.1:5000", CYAN), ("Python 3.10", "Python 3.10", GREEN), ("Podman", "Podman | Docker", PURPLE)]:
        if t >= cue_(7, ph):
            x = chip(d, x, 650, lab, col, font(28, True), 58) + 20
    if t >= cue_(7, "Built for"):
        x = 160
        for lab in ["Pentesters", "Security auditors", "DevSecOps teams"]:
            x = chip(d, x, 740, lab, BLUE, font(26, True), 54) + 16
        T(d, (160, 825), "proof, not screenshots", font(30, True, True), TXT)
    if t >= cue_(7, "Licensed as"):
        box(d, (160, 870, 1200, 940), fill=mix(PANEL, AMBER, 0.15), outline=AMBER, w=2, rad=14)
        T(d, (190, 905), "IBM Bob Security Engineering - internal standard", font(26, True), AMBER, "lm")


# ---------------------------------------------------------------- scene 9: idle + title

# Scene 9 - Sat 14 Nov 2026 17:45 CET
def scene9(img, d, t):
    tt = cue_(8, "HexStrike just hired")
    tcut = tt - 0.9
    if t >= tt:
        a = ease((t - tt) / 0.8)
        T(d, (960, 440), "HexStrike", font(200, True), mix(BLACK, WHITE, a), "mm")
        wd = 760 * ease((t - tt - 0.3) / 0.9)
        d.rectangle((960 - wd / 2, 560, 960 + wd / 2, 566), fill=CYAN)
        T(d, (960, 630), "Bob Never Sleeps (And Never Skips the Paperwork)", font(34), mix(BLACK, MUTED, ease((t - tt - 0.8) / 0.8)), "mm")
        T(d, (960, 700), "127.0.0.1:5000  |  150+ tools  |  signed authorization required", font(24, mono=True),
          mix(BLACK, CYAN, ease((t - tt - 1.2) / 0.8)), "mm")
        return
    if t >= tcut:
        d.rectangle((0, 0, W, H), fill=BLACK)
        return
    t_a, t_b = cue_(8, "The tools were never"), cue_(8, "Judgment was")
    p = ease((t - t_a) / max(0.5, t_b + 0.6 - t_a))
    box(d, (610, 250, 1310, 700), fill=PANEL2, outline=LINE, w=2, rad=22)
    T(d, (650, 285), "AGENT PERSONA", font(20, mono=True), MUTED)
    T(d, (646, 315), "Bob", font(140, True), WHITE)
    col = mix(GREEN, (70, 78, 90), p)
    light(d, (670, 560), 14, col, PANEL2, 1 - 0.85 * p)
    T(d, (710, 560), "ACTIVE" if p < 0.6 else "IDLE", font(28, True, True), col, "lm")
    T(d, (650, 630), "engagement closed - ledger sealed", font(22, mono=True), MUTED)


SCENE_FUNCS = [scene1, scene2, scene3, scene4, scene5, scene6, scene7, scene8, scene9]


# Cue helper bound to the loaded timeline - Sat 14 Nov 2026 17:45 CET
def cue_(i, phrase):
    return C.cue(i, phrase)


# ---------------------------------------------------------------- compositing

# Draw burned-in caption band - Sat 14 Nov 2026 17:45 CET
def caption(img, d, t):
    d.rectangle((0, 972, W, H), fill=(4, 7, 11))
    d.line((0, 972, W, 972), fill=LINE)
    for a, b, s in CAPS:
        if a - 0.05 <= t <= b + 0.2:
            f = font(34)
            lines, cur = [], ""
            for w in s.split():
                trial = (cur + " " + w).strip()
                if f.getlength(trial) > 1700 and cur:
                    lines.append(cur)
                    cur = w
                else:
                    cur = trial
            lines.append(cur)
            y0 = 1026 - (len(lines) - 1) * 24
            for k, ln in enumerate(lines):
                T(d, (960, y0 + k * 48), ln, f, TXT, "mm")
            break


# Render one frame as a PIL image - Sat 14 Nov 2026 17:45 CET
def render(fi):
    t = fi / FPS
    total = C.TL[-1]["end"] + 1.0
    i = max(k for k, sc in enumerate(C.TL) if sc["start"] <= t)
    sc = C.TL[i]
    ts, dur = t - sc["start"], sc["end"] - sc["start"]
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    SCENE_FUNCS[i](img, d, ts)
    f = 1.0
    if i > 0:
        f = min(f, ease(ts / 0.35))
    if i < len(C.TL) - 1:
        f = min(f, ease((dur - ts) / 0.35))
    else:
        f = min(f, ease((total - t) / 1.0))
    if f < 1:
        img = Image.blend(Image.new("RGB", (W, H), BLACK), img, f)
        d = ImageDraw.Draw(img)
    caption(img, d, t)
    return img


# Pool worker: frame index to raw bytes - Sat 14 Nov 2026 17:45 CET
def render_bytes(fi):
    return render(fi).tobytes()


# Initialise timeline and captions (also run in each worker) - Sat 14 Nov 2026 17:45 CET
def init():
    C.load_timeline()
    CAPS[:] = C.captions()


# Format seconds for SRT - Sat 14 Nov 2026 17:45 CET
def srt_time(s):
    ms = int(round(s * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


# Full render + mux - Sat 14 Nov 2026 17:45 CET
def main_render():
    init()
    C.OUT.mkdir(exist_ok=True)
    with open(C.OUT / "HexStrike_demo.srt", "w", encoding="utf-8") as f:
        for k, (a, b, s) in enumerate(CAPS, 1):
            f.write(f"{k}\n{srt_time(a)} --> {srt_time(b)}\n{s}\n\n")
    total = C.TL[-1]["end"] + 1.0
    n = int(total * FPS)
    out = C.OUT / "HexStrike_demo.mp4"
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(C.BUILD / "audio.wav"),
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(max(1, cpu_count() - 1), initializer=init) as pool:
        for k, frame in enumerate(pool.imap(render_bytes, range(n), chunksize=6)):
            proc.stdin.write(frame)
            if k % 240 == 0:
                C.log.info("frame %d/%d", k, n)
    proc.stdin.close()
    proc.wait()
    C.log.info("wrote %s", out)


# Preview a single frame - Sat 14 Nov 2026 17:45 CET
def main_still(sec, path):
    init()
    render(int(sec * FPS)).save(path)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "still":
        main_still(float(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else str(C.BUILD / "still.png"))
    else:
        main_render()
