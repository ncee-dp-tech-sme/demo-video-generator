# Shared drawing components for the IBM Bob client demo scenes (windows, terminal, Bob panel, cards).
#
# Change log
# Sat 14 Nov 2026 18:05 CET - Initial version.

from functools import lru_cache

from PIL import Image, ImageDraw

import demo_common as C
from build_video import (AMBER, BG, BLACK, BLUE, CYAN, GREEN, H, LINE, MUTED, PANEL, PANEL2, PURPLE, RED,
                         TXT, W, WHITE, blink, box, chip, clamp, ease, font, mix, typed)
from build_video import T as _T

IBM = (69, 137, 255)          # IBM-blue accent usable on dark backgrounds
IBM_DARK = (15, 98, 254)
CODE_BG = (11, 16, 23)
GH_BG = (13, 17, 23)
GH_LINE = (48, 54, 61)
SAFE_H = 972                  # caption band starts below this line


# Text helper that draws "→" as a vector arrow (the sans font has no arrow glyph) - Sat 14 Nov 2026 18:40 CET
def T(d, xy, s, f, fill=TXT, anchor="la"):
    if "→" not in s:
        return _T(d, xy, s, f, fill, anchor)
    parts = [p.strip() for p in s.split("→")]
    size = f.size
    pad, alen = size * 0.35, size * 0.8
    ws = [f.getlength(p) for p in parts]
    total = sum(ws) + (len(parts) - 1) * (alen + 2 * pad)
    x, y = xy
    x -= {"l": 0, "m": total / 2, "r": total}[anchor[0]]
    va = anchor[1]
    ymid = y if va == "m" else y + size * 0.45
    for k, p in enumerate(parts):
        d.text((x, y), p, font=f, fill=fill, anchor="l" + va)
        x += ws[k]
        if k < len(parts) - 1:
            x0, x1 = x + pad, x + pad + alen
            wd = max(2, size // 14)
            d.line((x0, ymid, x1, ymid), fill=fill, width=wd)
            d.polygon([(x1 + wd, ymid), (x1 - size * 0.25, ymid - size * 0.22), (x1 - size * 0.25, ymid + size * 0.22)],
                      fill=fill)
            x += alen + 2 * pad


# Cue lookup bound to a scene index (seconds relative to scene start) - Sat 14 Nov 2026 18:05 CET
def K(i):
    def cue(phrase, off=0.0):
        return max(0.0, C.cue(i, phrase) + off)
    return cue


# Eased 0..1 progress for an event starting at t0 - Sat 14 Nov 2026 18:05 CET
def prog(t, t0, dur=0.4):
    return ease((t - t0) / dur)


# Word-wrap text to a pixel width - Sat 14 Nov 2026 18:05 CET
def wrap(s, f, width):
    lines, cur = [], ""
    for w in s.split():
        trial = (cur + " " + w).strip()
        if f.getlength(trial) > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


# Cached dark gradient + grid backdrop - Sat 14 Nov 2026 18:05 CET
@lru_cache(maxsize=None)
def backdrop():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    for y in range(H):
        d.line((0, y, W, y), fill=mix((16, 24, 38), (6, 9, 14), y / H))
    for x in range(0, W, 80):
        d.line((x, 0, x, H), fill=(15, 22, 33))
    for y in range(0, H, 80):
        d.line((0, y, W, y), fill=(15, 22, 33))
    return img


# Paste the cached backdrop - Sat 14 Nov 2026 18:05 CET
def paint_backdrop(img):
    img.paste(backdrop())


# Scale a layer around its centre and crop back to size - Sat 14 Nov 2026 18:05 CET
def zoomed(layer, k):
    w, h = layer.size
    if k <= 1.0001:
        return layer
    big = layer.resize((int(w * k), int(h * k)), Image.Resampling.BILINEAR)
    x, y = (big.width - w) // 2, (big.height - h) // 2
    return big.crop((x, y, x + w, y + h))


# Window with title bar; returns the content rect - Sat 14 Nov 2026 18:05 CET
def win(d, rect, title, fill=PANEL, bar=(30, 40, 54), title_col=MUTED):
    x0, y0, x1, y1 = rect
    box(d, rect, fill=fill, outline=LINE, w=2, rad=14)
    d.rounded_rectangle((x0, y0, x1, y0 + 40), 14, fill=bar)
    d.rectangle((x0, y0 + 24, x1, y0 + 40), fill=bar)
    for k, c in enumerate([RED, AMBER, GREEN]):
        d.ellipse((x0 + 16 + k * 24, y0 + 13, x0 + 30 + k * 24, y0 + 27), fill=c)
    T(d, ((x0 + x1) / 2, y0 + 21), title, font(18), title_col, "mm")
    return (x0 + 2, y0 + 42, x1 - 2, y1 - 2)


# Terminal with timed lines; "$ " lines are typed. lines = [(text, colour, t_appear)] - Sat 14 Nov 2026 18:05 CET
def term(d, rect, lines, t, title="Terminal", fs=19, lh=28):
    cx0, cy0, cx1, cy1 = win(d, rect, title, fill=CODE_BG)
    f = font(fs, mono=True)
    vis = [(s, col, t0) for s, col, t0 in lines if t >= t0]
    rows = max(1, int((cy1 - cy0 - 20) // lh))
    for k, (s, col, t0) in enumerate(vis[-rows:]):
        if s.startswith("$ "):
            txt = typed(s, t - t0, 55)
            T(d, (cx0 + 18, cy0 + 14 + k * lh), "$", f, GREEN)
            T(d, (cx0 + 18 + f.getlength("$ "), cy0 + 14 + k * lh), txt[2:], f, TXT)
        else:
            T(d, (cx0 + 18, cy0 + 14 + k * lh), s, f, col)
    last_k = min(len(vis), rows)
    if blink(t) and vis:
        T(d, (cx0 + 18, cy0 + 14 + last_k * lh), "_", f, GREEN)
    return (cx0, cy0, cx1, cy1)


# Bob panel frame with mode pill; returns the content rect - Sat 14 Nov 2026 18:05 CET
def bob_panel(d, rect, mode="AGENT", title="IBM Bob"):
    cx0, cy0, cx1, cy1 = win(d, rect, title, fill=(14, 20, 30), bar=(20, 32, 56), title_col=IBM)
    col = PURPLE if mode == "PLAN" else IBM
    x = cx0 + 18
    T(d, (x, cy0 + 22), "Bob", font(26, True), TXT, "lm")
    chip(d, x + 70, cy0 + 4, f"{mode} MODE", col, font(18, True), h=36)
    d.line((cx0, cy0 + 50, cx1, cy0 + 50), fill=LINE)
    return (cx0, cy0 + 56, cx1, cy1)


# Checklist row with tick - Sat 14 Nov 2026 18:05 CET
def check(d, x, y, text, done=True, col=GREEN, f=None, w=None):
    f = f or font(24)
    box(d, (x, y, x + 30, y + 30), fill=mix(PANEL, col, 0.9) if done else None,
        outline=col if done else MUTED, w=2, rad=7)
    if done:
        d.line((x + 7, y + 16, x + 13, y + 22), fill=BG, width=4)
        d.line((x + 13, y + 22, x + 24, y + 8), fill=BG, width=4)
    lines = wrap(text, f, w) if w else [text]
    for k, ln in enumerate(lines):
        T(d, (x + 44, y + 15 + k * 30), ln, f, TXT if done else MUTED, "lm")
    return y + 30 + (len(lines) - 1) * 30


# Callout pill with fade-in - Sat 14 Nov 2026 18:05 CET
def callout(d, xy, text, col, t, t0, f=None, anchor="l"):
    p = prog(t, t0, 0.35)
    if p <= 0:
        return
    f = f or font(24, True)
    w = int(f.getlength(text)) + 44
    x, y = xy
    if anchor == "m":
        x -= w // 2
    bg = mix(BG, col, 0.22 * p)
    box(d, (x, y, x + w, y + 46), fill=bg, outline=mix(BG, col, p), w=2, rad=23)
    T(d, (x + w / 2, y + 23), text, f, mix(BG, col, p), "mm")


# Code lines inside a rect; lines = [(text, colour)] - Sat 14 Nov 2026 18:05 CET
def code(d, rect, lines, fs=20, lh=28, n0=1, gutter=True):
    x0, y0, x1, y1 = rect
    f = font(fs, mono=True)
    for k, item in enumerate(lines):
        s, col = item[0], item[1]
        y = y0 + k * lh
        if y + lh > y1:
            break
        bgc = item[2] if len(item) > 2 else None
        if bgc:
            d.rectangle((x0, y - 2, x1, y + lh - 4), fill=bgc)
        if gutter:
            T(d, (x0 + 44, y), str(n0 + k), f, (80, 92, 108), "ra")
        T(d, (x0 + 62, y), s, f, col)


# Slide-in lower third for the presenter name - Sat 14 Nov 2026 18:05 CET
def nameplate(d, t, t0=1.0, x=110, y=760):
    p = prog(t, t0, 0.6)
    if p <= 0:
        return
    off = int((1 - p) * -500)
    box(d, (x + off, y, x + off + 640, y + 120), fill=(10, 16, 26), outline=LINE, w=2, rad=10)
    d.rectangle((x + off, y, x + off + 10, y + 120), fill=IBM_DARK)
    T(d, (x + off + 40, y + 42), "Bobby", font(46, True), TXT, "lm")
    T(d, (x + off + 40, y + 88), "Enterprise Sales, IBM", font(28), MUTED, "lm")


# Persistent disclaimer label (top-right) - Sat 14 Nov 2026 18:05 CET
def disclaimer(d):
    f = font(17)
    s = "Stylised illustration of the workflow"
    w = int(f.getlength(s)) + 28
    box(d, (W - w - 24, 14, W - 24, 46), fill=(12, 18, 27), outline=LINE, w=1, rad=16)
    T(d, (W - 24 - w / 2, 30), s, f, MUTED, "mm")


# GitHub-workflow watermark (top-left) used throughout part 2 - Sat 14 Nov 2026 18:05 CET
def gh_mark(d):
    f = font(17, True)
    s = "GITHUB WORKFLOW"
    w = int(f.getlength(s)) + 52
    box(d, (24, 14, 24 + w, 46), fill=(12, 18, 27), outline=LINE, w=1, rad=16)
    d.ellipse((38, 22, 54, 38), fill=TXT)
    T(d, (66, 30), s, f, MUTED, "lm")


# GitHub-style page chrome with repo header; returns content rect - Sat 14 Nov 2026 18:05 CET
def gh_page(d, rect, url, repo=None, tab="Code", private=True):
    x0, y0, x1, y1 = rect
    box(d, rect, fill=GH_BG, outline=GH_LINE, w=2, rad=14)
    d.rounded_rectangle((x0, y0, x1, y0 + 44), 14, fill=(22, 27, 34))
    d.rectangle((x0, y0 + 28, x1, y0 + 44), fill=(22, 27, 34))
    box(d, (x0 + 20, y0 + 7, x1 - 20, y0 + 37), fill=GH_BG, rad=14)
    T(d, (x0 + 40, y0 + 22), url, font(16, mono=True), MUTED, "lm")
    y = y0 + 64
    if repo:
        T(d, (x0 + 26, y + 18), repo, font(26, True), (88, 166, 255), "lm")
        if private:
            chip(d, x0 + 36 + int(font(26, True).getlength(repo)), y + 2, "Private", MUTED, font(15, True), h=32)
        tx = x0 + 26
        for name in ["Code", "Issues", "Pull requests", "Actions"]:
            f = font(18, True if name == tab else False)
            T(d, (tx, y + 62), name, f, TXT if name == tab else MUTED, "lm")
            if name == tab:
                d.line((tx, y + 80, tx + f.getlength(name), y + 80), fill=AMBER, width=3)
            tx += int(f.getlength(name)) + 34
        d.line((x0, y + 84, x1, y + 84), fill=GH_LINE)
        y += 98
    return (x0 + 2, y, x1 - 2, y1 - 2)


# Full-width title card used for Part 1 / Part 2 - Sat 14 Nov 2026 18:05 CET
def title_card(img, d, t, part, name, sub, lit):
    paint_backdrop(img)
    a = prog(t, 0.3, 0.8)
    T(d, (960, 360), f"PART {part}", font(40, True), mix(BG, IBM, a), "mm")
    T(d, (960, 470), name, font(170, True), mix(BG, TXT, a), "mm")
    T(d, (960, 590), sub, font(38), mix(BG, MUTED, prog(t, 0.9, 0.8)), "mm")
    # progress strip
    for k, label in enumerate(["BUILD", "EVOLVE"]):
        x0 = 460 + k * 520
        on = k <= lit
        box(d, (x0, 800, x0 + 480, 830), fill=mix(PANEL, IBM_DARK, 0.9) if on else PANEL2, outline=LINE, w=1, rad=15)
        T(d, (x0 + 240, 815), label, font(20, True), WHITE if on else MUTED, "mm")
