# Scene engine for step 9 (video production): draws an animated mock screen for every scene of a storyboard
# (see storyboard.py): title cards, cards, checklists, terminal, browser, IDE with assistant panel, architecture flow,
# stats, scrolling feeds and split screens. Everything is drawn with Pillow; text typed, items revealed in step with the
# voice-over (words in the voice-over are matched to on-screen items), cursors move and click, arrows carry moving dots.
# Nothing here is product footage: screens are stylised illustrations built from the script text.
#
# Used by generic_video.py:  draw_scene(img, scene_index, seconds_into_scene, scene_seconds, spec, style) -> img
#
# Change log
# Sat 14 Nov 2026 21:49 CET - Initial version.
# Sat 14 Nov 2026 22:31 CET - Fit and wrap long headings, reserve vertical space, prevent badge collisions.

import math
import re

from PIL import Image, ImageDraw

import build_video as BV
import demo_common as C
from bob_ui import T, backdrop, prog, term, win, wrap
from build_video import (AMBER, BG, BLACK, BLUE, CYAN, GREEN, H, LINE, MUTED, PANEL, PANEL2, PURPLE, RED, TXT, W, WHITE,
                         blink, box, clamp, font, mix, typed)

IBM = (69, 137, 255)
RGB = {"cyan": CYAN, "blue": IBM, "green": GREEN, "amber": AMBER, "purple": PURPLE, "red": RED}
ORDER = list(RGB)
CYCLE = ["cyan", "blue", "green", "amber", "purple"]
SKEL, SKEL2 = (30, 42, 58), (22, 31, 44)
LABEL_LAYOUTS = ("terminal", "browser", "ide", "split", "feed")
_SCHED = {}


# --- helpers ---------------------------------------------------------------------------------------------------------

# Colour blended toward the background by alpha a - Sat 14 Nov 2026 21:49 CET
def fade(col, a, bg=BG):
    return mix(bg, col, clamp(a))


# Text width in pixels - Sat 14 Nov 2026 21:49 CET
def tw(f, s):
    return f.getlength(s)


# Shorten a string with "..." so it fits a pixel width - Sat 14 Nov 2026 21:49 CET
def clip(s, f, w):
    if tw(f, s) <= w:
        return s
    while s and tw(f, s + "...") > w:
        s = s[:-1]
    return s.rstrip() + "..."


# Wrap to at most n lines of a pixel width, last line clipped - Sat 14 Nov 2026 21:49 CET
def wrapn(s, f, w, n):
    lines = wrap(s, f, w) or [""]
    if len(lines) > n:
        lines = lines[:n]
        lines[-1] = lines[-1] + "..."
    return [clip(x, f, w) for x in lines]


# Largest font size (bold) from hi down to lo where the text fits one line - Sat 14 Nov 2026 21:49 CET
def fit_size(s, w, hi, lo, bold=True, mono=False):
    size = hi
    while size > lo and tw(font(size, bold, mono), s) > w:
        size -= 4
    return size


# Pill label with fade-in; returns the right edge - Sat 14 Nov 2026 21:49 CET
def pill(d, x, y, s, col, a=1.0, f=None, h=46, bg=BG):
    f = f or font(24, True)
    w = int(tw(f, s)) + 40
    box(d, (x, y, x + w, y + h), fill=mix(bg, col, 0.20 * a), outline=fade(col, a, bg), w=2, rad=h // 2)
    T(d, (x + w / 2, y + h / 2), s, f, fade(col, a, bg), "mm")
    return x + w


# Times (seconds into the scene) at which the items of a group appear.
# Words of each item are looked up in the voice-over; when every item is found in order those times are used,
# otherwise the items are spread evenly over the voice-over. lo/hi pick the part of the window (0..1) - Sat 14 Nov 2026 21:49 CET
# Words of each item are looked up in the voice-over; when every item is found in order those times are used - Sat Nov 14 22:31:51 CET 2026
def schedule(i, name, texts, cues=None, dur=10.0, lo=0.0, hi=1.0):
    key = (i, name, tuple(texts), tuple(cues or ()), lo, hi)
    if key in _SCHED:
        return _SCHED[key]
    n = len(texts)
    parts = C.TL[i]["parts"] if C.TL and i < len(C.TL) else []
    vo_end = max([p["t0"] + p["dur"] for p in parts] or [dur * 0.8])
    span = max(1.0, min(vo_end * 0.88, dur - 1.0) - 0.6)
    w0, w1 = 0.6 + span * lo, 0.6 + span * hi
    even = [w0 + (w1 - w0) * k / max(1, n) for k in range(n)]
    found = []
    for k, text in enumerate(texts):
        explicit = (cues or [None] * n)[k]
        words = sorted(set(re.findall(r"[A-Za-z][A-Za-z0-9]{3,}", text)), key=len, reverse=True)[:3]
        cands = [explicit] if explicit else [x for w in words for x in (w.lower(), w.lower()[:-2] if len(w) > 5 else w.lower())]
        t0 = None
        for phrase in cands:
            try:
                t0 = C.cue(i, phrase, 0.15)
                break
            except (KeyError, IndexError):
                continue
        found.append(t0)
    ok = n > 0 and all(f is not None for f in found) and all(b - a >= 0.25 for a, b in zip(found, found[1:]))
    out = found if ok else even
    _SCHED[key] = out
    return out


# Per-scene drawing context: time, scene index, colours, scheduling - Sat 14 Nov 2026 21:49 CET
class Ctx:
    def __init__(self, i, spec, t, dur, accent="cyan", key=""):
        self.i, self.spec, self.t, self.dur, self.accent, self.key = i, spec, t, dur, accent, key

    @property
    def acc(self):
        return RGB[self.accent]

    def color(self, name="", k=0):
        if name in RGB:
            return RGB[name]
        return RGB[CYCLE[(CYCLE.index(self.accent) + k) % len(CYCLE)] if self.accent in CYCLE else CYCLE[k % len(CYCLE)]]

    def times(self, name, texts, cues=None, lo=0.0, hi=1.0):
        return schedule(self.i, self.key + name, list(texts), cues, self.dur, lo, hi)

    def sub(self, spec, key):
        return Ctx(self.i, spec, self.t, self.dur, self.accent, key)


# Skeleton bars (honest placeholder content for UI areas the script says nothing about) - Sat 14 Nov 2026 21:49 CET
def bars(d, x, y, widths, h=14, gap=26, col=SKEL, a=1.0, bg=PANEL):
    for k, wd in enumerate(widths):
        d.rounded_rectangle((x, y + k * gap, x + wd, y + k * gap + h), h // 2, fill=mix(bg, col, a))


# Dim scrolling list behind a scene (backlog / feed feeling) - Sat 14 Nov 2026 21:49 CET
def feed_backdrop(d, t):
    base = int(t * 40 // 120)
    off = (t * 40) % 120
    for k in range(-1, 10):
        idx, y = k + base, int(k * 120 - off + 40)
        x0 = 380
        box(d, (x0, y, x0 + 1160, y + 96), fill=(14, 21, 31), outline=(24, 34, 48), w=2, rad=14)
        d.ellipse((x0 + 24, y + 34, x0 + 52, y + 62), outline=(36, 52, 74), width=3)
        wd = 300 + (idx * 97) % 520
        d.rounded_rectangle((x0 + 80, y + 28, x0 + 80 + wd, y + 44), 8, fill=(28, 40, 56))
        d.rounded_rectangle((x0 + 80, y + 56, x0 + 80 + wd // 2, y + 68), 6, fill=(21, 30, 43))
        box(d, (x0 + 1020, y + 30, x0 + 1120, y + 66), fill=(18, 27, 38), outline=(30, 44, 62), w=2, rad=18)


# Backdrop with drifting particles; "feed" adds the dim scrolling list - Sat 14 Nov 2026 21:49 CET
def paint_bg(img, d, t, kind):
    img.paste(backdrop())
    for k in range(16):
        x = (k * 151 + t * (7 + k % 5 * 3)) % W
        y = (k * 223 + t * (4 + k % 3 * 2)) % H
        r = 2 + k % 3
        d.ellipse((x - r, y - r, x + r, y + r), fill=(28, 42, 60))
    if kind == "feed":
        feed_backdrop(d, t)


# --- layouts ---------------------------------------------------------------------------------------------------------

# Big title, kicker, subtitle and optional progress strip - Sat 14 Nov 2026 21:49 CET
def L_title(img, d, S, r):
    sp, t = S.spec, S.t
    x0, y0, x1, y1 = r
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    title, steps = sp.get("title", ""), sp.get("steps") or []
    maxw = x1 - x0 - 160
    size = fit_size(title, maxw, 170, 64)
    f = font(size, True)
    lines = [title] if tw(f, title) <= maxw else wrapn(title, f, maxw, 3)
    lh = int(size * 1.14)
    top = cy - (60 if steps else 20) - lh * len(lines) // 2
    a_k, a_t, a_s = prog(t, 0.2, 0.6), prog(t, 0.45, 0.8), prog(t, 1.1, 0.8)
    if sp.get("kicker"):
        T(d, (cx, top - 56 + int((1 - a_k) * 16)), sp["kicker"], font(42, True), fade(S.acc, a_k), "mm")
    for k, ln in enumerate(lines):
        T(d, (cx, top + k * lh + lh // 2 + int((1 - a_t) * 26)), ln, f, fade(TXT, a_t), "mm")
    ybar = top + lh * len(lines) + 22
    wd = 560 * prog(t, 0.9, 0.9)
    d.rectangle((cx - wd / 2, ybar, cx + wd / 2, ybar + 6), fill=S.acc)
    if sp.get("subtitle"):
        for k, ln in enumerate(wrapn(sp["subtitle"], font(40), 1400, 2)):
            T(d, (cx, ybar + 56 + k * 52), ln, font(40), fade(MUTED, a_s), "mm")
    if steps:
        n = len(steps)
        w = int(min(480, (1100 - (n - 1) * 40) / n))
        sx = cx - (n * w + (n - 1) * 40) // 2
        for k, label in enumerate(steps):
            on = k <= sp.get("active", 0)
            x = sx + k * (w + 40)
            box(d, (x, y1 - 150, x + w, y1 - 116), fill=mix(BG, S.acc, 0.55) if on else PANEL2, outline=LINE, w=1, rad=17)
            T(d, (x + w / 2, y1 - 133), label, font(22, True), WHITE if on else MUTED, "mm")


# Cards that appear one after another - Sat 14 Nov 2026 21:49 CET
def L_cards(img, d, S, r):
    cards = S.spec["cards"]
    n = len(cards)
    x0, y0, x1, y1 = r
    cols = n if n <= 4 else math.ceil(n / 2)
    rows = math.ceil(n / cols)
    gap = 28
    has_text = any(c.get("text") for c in cards)
    cw = (x1 - x0 - 40 - gap * (cols - 1)) // cols
    ch = int(min((y1 - y0 - gap * (rows - 1)) / rows, (440 if has_text else 240) if rows == 1 else 320))
    gx0 = (x0 + x1 - (cols * cw + (cols - 1) * gap)) // 2
    gy0 = (y0 + y1 - (rows * ch + (rows - 1) * gap)) // 2
    ts = S.times("cards", [c.get("title") or c.get("text", "") for c in cards], [c.get("cue") for c in cards])
    latest = max([k for k, t0 in enumerate(ts) if S.t >= t0] or [-1])
    ft, fx = (38 if cols <= 3 else 32 if cols <= 4 else 28), (26 if cols <= 3 else 23)
    for k, c in enumerate(cards):
        p = prog(S.t, ts[k], 0.5)
        if p <= 0:
            continue
        col = S.color(c.get("color", ""), k)
        x = gx0 + (k % cols) * (cw + gap)
        y = gy0 + (k // cols) * (ch + gap) + int((1 - p) * 36)
        pulse = clamp(1 - (S.t - ts[k]) / 1.4) if k == latest else 0
        box(d, (x, y, x + cw, y + ch), fill=mix(BG, mix(PANEL, col, 0.12), p),
            outline=mix(fade(col, p), WHITE, 0.45 * pulse), w=4 if pulse > 0 else 2, rad=22)
        d.rounded_rectangle((x + 24, y + 0, x + cw - 24, y + 8), 4, fill=fade(col, p))
        ty = y + 34
        if n > 1 and cw >= 240 and has_text:
            d.ellipse((x + 28, ty, x + 76, ty + 48), fill=mix(BG, mix(PANEL, col, 0.45), p), outline=fade(col, p), width=2)
            T(d, (x + 52, ty + 24), str(k + 1), font(26, True), fade(WHITE, p), "mm")
            ty += 70
        f = font(ft, True)
        tl = wrapn(c.get("title", ""), f, cw - 56, 3)
        if not has_text:
            ty = y + (ch - len(tl) * int(ft * 1.25)) // 2
        for ln in tl:
            T(d, (x + 28, ty), ln, f, fade(TXT, p))
            ty += int(ft * 1.25)
        if c.get("text"):
            ty += 8
            for ln in wrapn(c["text"], font(fx), cw - 56, 5 if rows == 1 else 3):
                T(d, (x + 28, ty), ln, font(fx), fade(MUTED, p))
                ty += int(fx * 1.35)


# Checklist whose boxes tick one by one - Sat 14 Nov 2026 21:49 CET
def L_checklist(img, d, S, r):
    items = S.spec["items"]
    n = len(items)
    x0, y0, x1, y1 = r
    rh = 100 if n <= 5 else 78 if n <= 7 else 64
    fs = 44 if n <= 5 else 36 if n <= 7 else 30
    bw = min(1400, x1 - x0 - 80)
    bx, by = (x0 + x1 - bw) // 2, (y0 + y1 - n * rh) // 2
    ts = S.times("items", [i["text"] for i in items], [i.get("cue") for i in items])
    for k, it in enumerate(items):
        p = prog(S.t, ts[k], 0.4)
        y = by + k * rh + int((1 - p) * 20)
        if p > 0:
            box(d, (bx, y, bx + bw, y + rh - 14), fill=mix(BG, PANEL, p), outline=fade(LINE, p), w=2, rad=16)
        s = rh - 14
        cb = (bx + 20, y + (s - 44) // 2, bx + 64, y + (s - 44) // 2 + 44)
        box(d, cb, fill=None, outline=fade(MUTED if S.t < ts[k] + 0.35 else GREEN, max(p, 0.25)), w=3, rad=10)
        q = prog(S.t, ts[k] + 0.35, 0.3)
        if q > 0:
            box(d, cb, fill=mix(PANEL, GREEN, 0.9 * q), outline=GREEN, w=3, rad=10)
            d.line((cb[0] + 10, cb[1] + 24, cb[0] + 19, cb[1] + 33), fill=BG, width=5)
            d.line((cb[0] + 19, cb[1] + 33, cb[0] + 35, cb[1] + 11), fill=BG, width=5)
        T(d, (bx + 96, y + s // 2), clip(it["text"], font(fs, True), bw - 130), font(fs, True), fade(TXT, p), "lm")


# Colour of a terminal output line - Sat 14 Nov 2026 21:49 CET
def line_color(s):
    low = s.lower()
    if re.search(r"error|fail|denied|blocked|refused", low):
        return RED
    if re.search(r"warn", low):
        return AMBER
    if re.search(r"passed|\bok\b|done|success|ready|created|pushed|listening|complete|online|green", low):
        return GREEN
    return TXT


# Terminal where commands are typed and output lines follow - Sat 14 Nov 2026 21:49 CET
def L_terminal(img, d, S, r):
    lines = S.spec["lines"]
    x0, y0, x1, y1 = r
    full = x1 - x0 > 1200
    fs = 28 if full else 21
    lh = int(fs * 1.5)
    groups = []
    for ln in lines:
        if ln.startswith("$ ") or not groups:
            groups.append([ln])
        else:
            groups[-1].append(ln)
    gts = S.times("term", [g[0][2:] if g[0].startswith("$ ") else g[0] for g in groups])
    timed, prev_end = [], 0.0
    for g, gt in zip(groups, gts):
        cur = max(gt, prev_end)
        for ln in g:
            timed.append((ln, GREEN if ln.startswith("$ ") else line_color(ln), cur))
            cur += (len(ln) / 55 + 0.45) if ln.startswith("$ ") else 0.3
        prev_end = cur + 0.2
    h = int(min(y1 - y0, max(380, (len(lines) + 1) * lh + 130))) if full else (y1 - y0)
    top = y0 + (y1 - y0 - h) // 2
    left, right = (x0 + 100, x1 - 100) if full else (x0, x1)
    term(d, (left, top, right, top + h), timed, S.t, S.spec.get("window_title") or "Terminal", fs=fs, lh=lh)


# Skeleton page content (tiles and text lines) for browser windows - Sat 14 Nov 2026 21:49 CET
def skeleton_page(d, rect, t, a=1.0):
    x0, y0, x1, y1 = rect
    tile = (x1 - x0 - 2 * 24) // 3
    for k in range(3):
        tx = x0 + k * (tile + 24)
        box(d, (tx, y0, tx + tile, y0 + 130), fill=mix(PANEL, PANEL2, 0.8 * a), outline=fade(LINE, a, PANEL), w=2, rad=14)
        bars(d, tx + 22, y0 + 26, [90 + 30 * k], 12, a=a)
        bars(d, tx + 22, y0 + 62, [tile - 130], 30, a=a)
    bars(d, x0, y0 + 170, [x1 - x0 - 300, x1 - x0 - 140, x1 - x0 - 420, x1 - x0 - 220, x1 - x0 - 360], 14, 32, a=a)


# Mouse pointer with click ripple - Sat 14 Nov 2026 21:49 CET
def pointer(d, x, y, click_p=0.0):
    if click_p > 0:
        rr = 14 + 46 * click_p
        d.ellipse((x - rr, y - rr, x + rr, y + rr), outline=mix(PANEL, WHITE, 1 - click_p), width=3)
    d.polygon([(x, y), (x, y + 34), (x + 9, y + 26), (x + 17, y + 42), (x + 24, y + 38), (x + 16, y + 23), (x + 28, y + 23)],
              fill=WHITE, outline=BLACK)


# Browser window: URL bar, optional nav, heading, rows, button with moving pointer, modal - Sat 14 Nov 2026 21:49 CET
def L_browser(img, d, S, r):
    sp, t = S.spec, S.t
    x0, y0, x1, y1 = r
    full = x1 - x0 > 1200
    box(d, r, fill=PANEL, outline=LINE, w=2, rad=18)
    d.rounded_rectangle((x0, y0, x1, y0 + 56), 18, fill=(30, 40, 54))
    d.rectangle((x0, y0 + 30, x1, y0 + 56), fill=(30, 40, 54))
    for k, c in enumerate([RED, AMBER, GREEN]):
        d.ellipse((x0 + 22 + k * 28, y0 + 20, x0 + 38 + k * 28, y0 + 36), fill=c)
    box(d, (x0 + 140, y0 + 10, x1 - 140, y0 + 46), fill=BG, rad=18)
    url = sp.get("url") or "localhost"
    T(d, (x0 + 170, y0 + 28), clip(url, font(22, mono=True), x1 - x0 - 360), font(22, mono=True), MUTED, "lm")
    cx0, cy0, cx1, cy1 = x0 + 2, y0 + 56, x1 - 2, y1 - 2
    pad = 40 if full else 24
    mx0 = cx0
    if sp.get("nav"):
        d.rectangle((cx0, cy0, cx0 + 250, cy1), fill=(13, 19, 27))
        T(d, (cx0 + 28, cy0 + 40), "APP", font(26, True), S.acc)
        for k, s in enumerate(sp["nav"]):
            if k == 0:
                box(d, (cx0 + 14, cy0 + 84, cx0 + 236, cy0 + 130), fill=mix(PANEL, S.acc, 0.15), rad=10)
            T(d, (cx0 + 34, cy0 + 108 + k * 56), clip(s, font(24), 190), font(24), TXT if k == 0 else MUTED, "lm")
        mx0 = cx0 + 250
    y = cy0 + pad
    if sp.get("heading"):
        a = prog(t, 0.3, 0.5)
        hf = font(fit_size(sp["heading"], cx1 - mx0 - 2 * pad, 64 if full else 40, 28), True)
        T(d, (mx0 + pad, y + int((1 - a) * 14)), sp["heading"], hf, fade(TXT, a, PANEL))
        y += hf.size + 18
        if not sp.get("rows"):
            BV.light(d, (mx0 + pad + 14, y + 20), 9, GREEN, PANEL, 0.75 + 0.25 * math.sin(t * 4))
            T(d, (mx0 + pad + 40, y + 20), "ACTIVE", font(24, True, True), fade(GREEN, a, PANEL), "lm")
            y += 60
    area = (mx0 + pad, y + 10, cx1 - pad, cy1 - pad)
    rows = sp.get("rows") or []
    if rows:
        ts = S.times("rows", [x["text"] for x in rows], [x.get("cue") for x in rows])
        rh = 84 if full else 66
        for k, row in enumerate(rows):
            p = prog(t, ts[k], 0.4)
            yy = area[1] + k * (rh + 14) + int((1 - p) * 18)
            if yy + rh > area[3]:
                break
            if p > 0:
                col = S.color(row.get("color", ""), k)
                box(d, (area[0], yy, area[2], yy + rh), fill=mix(PANEL, PANEL2, p), outline=fade(LINE, p, PANEL), w=2, rad=14)
                d.ellipse((area[0] + 22, yy + rh / 2 - 9, area[0] + 40, yy + rh / 2 + 9), fill=fade(col, p, PANEL))
                T(d, (area[0] + 64, yy + rh / 2), clip(row["text"], font(28 if full else 22), area[2] - area[0] - 300), font(28 if full else 22), fade(TXT, p, PANEL), "lm")
                if row.get("chip"):
                    pill(d, area[2] - 20 - int(tw(font(20, True), row["chip"])) - 40, yy + rh // 2 - 20, row["chip"], col, p, font(20, True), 40, PANEL)
    else:
        skeleton_page(d, area, t)
    bt = None
    if sp.get("button"):
        bt = S.times("button", [sp["button"]], lo=0.2, hi=0.6)[0]
        bw_ = int(tw(font(28, True), sp["button"])) + 70
        bx = cx1 - pad - bw_
        by = cy1 - pad - 64
        down = prog(t, bt, 0.15) * (1 - prog(t, bt + 0.3, 0.2))
        box(d, (bx, by + int(4 * down), bx + bw_, by + 64 + int(4 * down)), fill=mix(S.acc, BLACK, 0.45 + 0.2 * down), outline=S.acc, w=2, rad=14)
        T(d, (bx + bw_ / 2, by + 32 + int(4 * down)), sp["button"], font(28, True), WHITE, "mm")
        mv = prog(t, bt - 1.3, 1.1)
        if t < bt + 1.2:
            px, py = (cx1 - 200) + (bx + bw_ // 2 - (cx1 - 200)) * mv, (cy0 + 300) + (by + 32 - (cy0 + 300)) * mv
            pointer(d, px, py, clamp((t - bt) / 0.6) if t >= bt else 0)
    modal = sp.get("modal")
    if modal:
        mt = (bt + 0.5) if bt is not None else S.times("modal", [modal.get("title") or modal.get("text")], lo=0.25, hi=0.7)[0]
        p = prog(t, mt, 0.4)
        if p > 0:
            reg = (cx0, cy0, cx1, cy1)
            img.paste(Image.blend(img.crop(reg), Image.new("RGB", (reg[2] - reg[0], reg[3] - reg[1]), BLACK), 0.55 * p), reg[:2])
            col = S.color(modal.get("color", "red"))
            mw, mh = min(760, cx1 - cx0 - 120), 300 if modal.get("text") else 230
            mx, my = (cx0 + cx1 - mw) // 2, (cy0 + cy1 - mh) // 2 + int((1 - p) * 40)
            box(d, (mx, my, mx + mw, my + mh), fill=mix(BG, (20, 27, 38), p), outline=fade(col, p), w=4, rad=22)
            T(d, (mx + 40, my + 56), clip(modal.get("title", ""), font(40, True), mw - 80), font(40, True), fade(TXT, p), "lm")
            for k, ln in enumerate(wrapn(modal.get("text", ""), font(28), mw - 80, 3)):
                T(d, (mx + 40, my + 118 + k * 38), ln, font(28), fade(MUTED, p), "lm")
            bl = modal.get("button") or "Continue"
            bwd = int(tw(font(26, True), bl)) + 60
            box(d, (mx + mw - 40 - bwd, my + mh - 84, mx + mw - 40, my + mh - 28), fill=mix(BG, col, 0.5 * p), outline=fade(col, p), w=2, rad=14)
            T(d, (mx + mw - 40 - bwd / 2, my + mh - 56), bl, font(26, True), fade(WHITE, p), "mm")


# Syntax colour spans for one code line - Sat 14 Nov 2026 21:49 CET
CODE_KW = re.compile(r"\b(def|class|return|import|from|const|let|var|function|if|else|elif|for|while|async|await|try|except|new|True|False|None|true|false)\b")
CODE_STR = re.compile(r"\"[^\"]*\"|'[^']*'")


# Draw one code line with simple colouring (fixed-width font) - Sat 14 Nov 2026 21:49 CET
def code_line(d, x, y, s, f, tint=None):
    cw = tw(f, "M")
    cols = [TXT] * len(s)
    for m in CODE_KW.finditer(s):
        cols[m.start():m.end()] = [(198, 120, 221)] * (m.end() - m.start())
    for m in CODE_STR.finditer(s):
        cols[m.start():m.end()] = [(152, 195, 121)] * (m.end() - m.start())
    if s.lstrip().startswith(("#", "//")):
        cols = [MUTED] * len(s)
    for k, ch in enumerate(s):
        d.text((x + k * cw, y), ch, font=f, fill=cols[k])


# File colour by extension - Sat 14 Nov 2026 21:49 CET
def file_color(name):
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    return {"py": IBM, "js": AMBER, "ts": IBM, "html": RED, "sh": GREEN, "json": AMBER, "md": MUTED, "yaml": PURPLE,
            "yml": PURPLE, "txt": MUTED, "css": PURPLE}.get(ext, CYAN if name.endswith("/") else MUTED)


# IDE: file tree, editor with typed code, assistant panel with prompt and plan, terminal pane - Sat 14 Nov 2026 21:49 CET
def L_ide(img, d, S, r):
    sp, t = S.spec, S.t
    panel, term_lines = sp.get("panel") or {}, sp.get("terminal") or []
    files = sp.get("files") or []
    code = (sp.get("editor") or {}).get("code") or []
    cx0, cy0, cx1, cy1 = win(d, r, "Workspace", fill=(12, 18, 27))
    pw = 560 if panel else 0
    treew = 300
    th = 260 if term_lines else 0
    # file tree
    d.rectangle((cx0, cy0, cx0 + treew, cy1), fill=(10, 15, 22))
    T(d, (cx0 + 20, cy0 + 24), "EXPLORER", font(16, True, True), MUTED, "lm")
    if files:
        fts = S.times("files", files, lo=0.0, hi=0.7)
        for k, name in enumerate(files):
            p = prog(t, fts[k], 0.3)
            yy = cy0 + 56 + k * 33
            if p <= 0 or yy > cy1 - 30:
                continue
            col = S.color("cyan") if name.endswith("/") else file_color(name)
            d.rectangle((cx0 + 22, yy + 8, cx0 + 34, yy + 20), fill=fade(col, p, (10, 15, 22)))
            T(d, (cx0 + 46 + int((1 - p) * 14), yy + 14), clip(name, font(19, mono=True), treew - 66), font(19, mono=True),
              fade(TXT, p, (10, 15, 22)), "lm")
    else:
        bars(d, cx0 + 22, cy0 + 60, [150, 190, 120, 170, 140, 100, 160], 12, 34, bg=(10, 15, 22))
    # editor
    ex0, ex1, ey1 = cx0 + treew, cx1 - pw, cy1 - th
    d.rectangle((ex0, cy0, ex1, cy0 + 44), fill=(16, 23, 33))
    tab = (sp.get("editor") or {}).get("file") or (files[0] if files else "main")
    box(d, (ex0 + 10, cy0 + 6, ex0 + 40 + int(tw(font(19, mono=True), tab)) + 20, cy0 + 44), fill=(12, 18, 27), rad=8)
    T(d, (ex0 + 24, cy0 + 26), clip(tab, font(19, mono=True), 420), font(19, mono=True), TXT, "lm")
    f = font(22, mono=True)
    lh = 32
    rows = max(1, int((ey1 - cy0 - 70) // lh))
    if code:
        cts = S.times("code", code, lo=0.1, hi=0.8)
        for k, ln in enumerate(code[:rows]):
            p = prog(t, cts[k], 0.2)
            if p <= 0:
                continue
            y = cy0 + 60 + k * lh
            diffy = not tab.lower().endswith((".md", ".txt", ".yaml", ".yml"))     # "- item" in these files is a bullet, not a removed line
            tint = (30, 70, 44) if diffy and ln.startswith("+") else (86, 34, 38) if diffy and ln.startswith("-") else None
            if tint:
                d.rectangle((ex0 + 1, y - 3, ex1 - 1, y + lh - 5), fill=tint)
            T(d, (ex0 + 52, y), str(k + 1), f, (80, 92, 108), "ra")
            code_line(d, ex0 + 70, y, clip(typed(ln, t - cts[k], 70), f, ex1 - ex0 - 100), f)
    else:
        n = min(rows, 14)
        add_t = max(1.5, S.dur * 0.45)
        for k in range(n):
            y = cy0 + 60 + k * lh
            if prog(t, 0.4 + k * 0.12, 0.3) <= 0:
                continue
            wd = [260, 420, 340, 180, 520, 300, 240, 460, 380, 200, 480, 320, 280, 410][k % 14]
            hl = 4 <= k <= 8 and t >= add_t
            if hl:
                d.rectangle((ex0 + 1, y - 3, ex1 - 1, y + lh - 5), fill=mix((12, 18, 27), (30, 70, 44), prog(t, add_t, 0.5)))
            T(d, (ex0 + 52, y + 4), str(k + 1), font(18, mono=True), (60, 72, 88), "ra")
            d.rounded_rectangle((ex0 + 70 + (30 if k % 4 == 1 else 0), y + 6, ex0 + 70 + (30 if k % 4 == 1 else 0) + min(wd, ex1 - ex0 - 140), y + 18),
                                6, fill=(40, 60, 84) if hl else SKEL)
    # terminal pane
    if term_lines:
        groups = []
        for ln in term_lines:
            if ln.startswith("$ ") or not groups:
                groups.append([ln])
            else:
                groups[-1].append(ln)
        gts = S.times("iterm", [g[0][2:] if g[0].startswith("$ ") else g[0] for g in groups], lo=0.25, hi=0.9)
        timed, prev = [], 0.0
        for g, gt in zip(groups, gts):
            cur = max(gt, prev)
            for ln in g:
                timed.append((ln, GREEN if ln.startswith("$ ") else line_color(ln), cur))
                cur += (len(ln) / 55 + 0.4) if ln.startswith("$ ") else 0.3
            prev = cur + 0.15
        term(d, (ex0, ey1, ex1, cy1 + 2), timed, t, "Terminal", fs=19, lh=27)
    # assistant panel
    if panel:
        px0 = cx1 - pw
        d.rectangle((px0, cy0, cx1, cy1), fill=(14, 20, 30))
        d.line((px0, cy0, px0, cy1), fill=LINE)
        T(d, (px0 + 22, cy0 + 28), clip(panel.get("title") or "Assistant", font(26, True), 250), font(26, True), TXT, "lm")
        if panel.get("mode"):
            mcol = PURPLE if panel["mode"] == "PLAN" else IBM
            pill(d, px0 + 22 + int(tw(font(26, True), clip(panel.get("title") or "Assistant", font(26, True), 250))) + 16, cy0 + 8,
                 panel["mode"] + " MODE", mcol, 1.0, font(17, True), 38, (14, 20, 30))
        d.line((px0, cy0 + 58, cx1, cy0 + 58), fill=LINE)
        y = cy0 + 78
        msgs = panel.get("messages") or []
        mts = S.times("msgs", msgs, lo=0.0, hi=0.5) if msgs else []
        for k, m in enumerate(msgs):
            p = prog(t, mts[k], 0.3)
            if p <= 0:
                continue
            fm = font(21)
            lines = wrapn(typed(m, t - mts[k], 80) if k == 0 else m, fm, pw - 90, 7)
            bh = len(lines) * 29 + 26
            user = k == 0
            bx = px0 + (36 if user else 20)
            box(d, (bx, y, bx + pw - 56, y + bh), fill=mix((14, 20, 30), IBM if user else PANEL2, 0.30 if user else 1.0),
                outline=fade(IBM if user else LINE, p, (14, 20, 30)), w=2, rad=16)
            for j, ln in enumerate(lines):
                T(d, (bx + 18, y + 14 + j * 29), ln, fm, fade(TXT, p, (14, 20, 30)))
            y += bh + 18
        plan = panel.get("plan") or []
        if plan:
            pts = S.times("plan", plan, lo=0.35, hi=0.9)
            T(d, (px0 + 24, y + 12), "PLAN", font(17, True, True), MUTED, "lm")
            y += 36
            for k, item in enumerate(plan):
                p = prog(t, pts[k], 0.3)
                if y + 36 > cy1 - 20:
                    break
                if p > 0:
                    done = t >= pts[k] + 0.5
                    box(d, (px0 + 24, y, px0 + 52, y + 28), fill=mix((14, 20, 30), GREEN, 0.9) if done else None,
                        outline=GREEN if done else fade(MUTED, p, (14, 20, 30)), w=2, rad=7)
                    if done:
                        d.line((px0 + 31, y + 15, px0 + 37, y + 21), fill=BG, width=4)
                        d.line((px0 + 37, y + 21, px0 + 47, y + 7), fill=BG, width=4)
                    T(d, (px0 + 66, y + 14), clip(item, font(22, mono=True), pw - 100), font(22, mono=True), fade(TXT, p, (14, 20, 30)), "lm")
                y += 38


# Architecture flow: nodes in a row, arrows with moving dots, chips below - Sat 14 Nov 2026 21:49 CET
def L_flow(img, d, S, r):
    nodes = S.spec["nodes"]
    n = len(nodes)
    x0, y0, x1, y1 = r
    gap = 130 if n <= 3 else 90 if n == 4 else 60
    nw = min(440, (x1 - x0 - 60 - gap * (n - 1)) // n)
    nh = 250
    sx = (x0 + x1 - (n * nw + (n - 1) * gap)) // 2
    cy = (y0 + y1) // 2 - 40
    ts = S.times("nodes", [nd["label"] for nd in nodes], [nd.get("cue") for nd in nodes])
    for k, nd in enumerate(nodes):
        p = prog(S.t, ts[k], 0.5)
        x = sx + k * (nw + gap)
        if k > 0 and S.t >= ts[k] + 0.2:           # arrow from previous node
            ax0, ax1 = x - gap + 10, x - 14
            ap = prog(S.t, ts[k] + 0.2, 0.5)
            e = ax0 + (ax1 - ax0) * ap
            d.line((ax0, cy, e, cy), fill=S.acc, width=5)
            if ap > 0.95:
                d.polygon([(ax1 + 4, cy), (ax1 - 20, cy - 14), (ax1 - 20, cy + 14)], fill=S.acc)
                for j in range(3):
                    q = ((S.t - ts[k]) * 0.7 + j / 3) % 1
                    px = ax0 + (ax1 - 24 - ax0) * q
                    d.ellipse((px - 7, cy - 7, px + 7, cy + 7), fill=WHITE)
        if p <= 0:
            continue
        col = S.color(nd.get("color", ""), k)
        yo = int((1 - p) * 40)
        box(d, (x, cy - nh // 2 + yo, x + nw, cy + nh // 2 + yo), fill=mix(BG, mix(PANEL, col, 0.14), p), outline=fade(col, p), w=3, rad=24)
        f = font(fit_size(nd["label"], nw - 40, 52, 26), True)
        lines = [nd["label"]] if tw(f, nd["label"]) <= nw - 40 else wrapn(nd["label"], font(30, True), nw - 40, 3)
        ff = f if len(lines) == 1 else font(30, True)
        ty = cy + yo - (len(lines) * int(ff.size * 1.2)) // 2 - (20 if nd.get("sub") else 0) + int(ff.size * 0.6)
        for ln in lines:
            T(d, (x + nw / 2, ty), ln, ff, fade(WHITE, p), "mm")
            ty += int(ff.size * 1.2)
        if nd.get("sub"):
            T(d, (x + nw / 2, cy + yo + nh // 2 - 44), clip(nd["sub"], font(22, mono=True), nw - 30), font(22, mono=True), fade(col, p), "mm")
    chips = S.spec.get("chips") or []
    if chips:
        cts = S.times("chips", chips, lo=0.4, hi=1.0)
        xx = x0 + 100
        for k, c in enumerate(chips):
            if S.t >= cts[k]:
                xx = pill(d, xx, cy + nh // 2 + 90, c, S.color("", k), prog(S.t, cts[k], 0.3), font(30, True), 64) + 24


# Big numbers with count-up - Sat 14 Nov 2026 21:49 CET
def L_stats(img, d, S, r):
    stats = S.spec["stats"]
    n = len(stats)
    x0, y0, x1, y1 = r
    colw = (x1 - x0 - 60) // n
    ts = S.times("stats", [s["label"] or s["value"] for s in stats], [s.get("cue") for s in stats])
    for k, st in enumerate(stats):
        p = prog(S.t, ts[k], 0.6)
        if p <= 0:
            continue
        col = S.color(st.get("color", ""), k)
        cx = x0 + 30 + colw * k + colw // 2
        cy = (y0 + y1) // 2 - 30
        val = st["value"]
        m = re.fullmatch(r"(\d[\d,]*)(\D*)", val)
        if m:
            target = int(m.group(1).replace(",", ""))
            cur = int(target * prog(S.t, ts[k], 1.2))
            val = (f"{cur:,}" if "," in m.group(1) else str(cur)) + m.group(2)
        size = fit_size(st["value"], colw - 60, 280 if n == 1 else 170, 70, True)
        T(d, (cx, cy + int((1 - p) * 30)), val, font(size, True), fade(col, p), "mm")
        wd = min(colw - 120, 520) * prog(S.t, ts[k] + 0.3, 0.8)
        d.rectangle((cx - wd / 2, cy + size // 2 + 24, cx + wd / 2, cy + size // 2 + 30), fill=fade(col, p))
        if st.get("label"):
            for j, ln in enumerate(wrapn(st["label"], font(52 if n == 1 else 38, True), colw - 60, 2)):
                T(d, (cx, cy + size // 2 + 80 + j * (62 if n == 1 else 46)), ln, font(52 if n == 1 else 38, True), fade(TXT, p), "mm")


# Scrolling table / issue list with skeleton rows - Sat 14 Nov 2026 21:49 CET
def L_feed(img, d, S, r):
    sp, t = S.spec, S.t
    x0, y0, x1, y1 = r
    cx0, cy0, cx1, cy1 = win(d, (x0 + 60, y0 + 10, x1 - 60, y1 - 10), sp.get("title") or "Records", fill=(12, 18, 27))
    cols = sp.get("columns") or []
    hy = cy0
    if cols:
        d.rectangle((cx0, cy0, cx1, cy0 + 56), fill=PANEL2)
        cw = (cx1 - cx0 - 60) / len(cols)
        for k, c in enumerate(cols):
            T(d, (cx0 + 30 + k * cw, cy0 + 28), clip(c, font(24, True, True), cw - 20), font(24, True, True), S.acc, "lm")
        hy = cy0 + 56
    items = sp.get("items") or []
    rh = 84
    speed = 55
    base = int(t * speed // rh)
    off = (t * speed) % rh
    hl = sp.get("highlight")
    for k in range(-1, int((cy1 - hy) // rh) + 2):
        y = int(hy + k * rh - off)
        idx = k + base
        if y < hy - 1 or y + rh > cy1 + 1:
            continue
        a = prog(t, 0.3, 0.6)
        if hl is not None and idx % max(1, len(items) or 7) == hl:
            d.rectangle((cx0 + 2, y, cx1 - 2, y + rh - 2), fill=mix((12, 18, 27), S.acc, 0.14))
        if items:
            it = items[idx % len(items)]
            col = S.color(it.get("color", ""), idx)
            d.ellipse((cx0 + 30, y + rh / 2 - 9, cx0 + 48, y + rh / 2 + 9), fill=fade(col, a, (12, 18, 27)))
            T(d, (cx0 + 72, y + rh / 2), clip(it["text"], font(28), cx1 - cx0 - 360), font(28), fade(TXT, a, (12, 18, 27)), "lm")
            if it.get("chip"):
                pill(d, cx1 - 40 - int(tw(font(20, True), it["chip"])) - 40, y + rh // 2 - 20, it["chip"], col, a, font(20, True), 40, (12, 18, 27))
        elif cols:
            cw = (cx1 - cx0 - 60) / len(cols)
            for j in range(len(cols)):
                wd = int(cw * (0.35 + 0.45 * (((idx + 1) * (j + 3) * 37) % 100) / 100))
                bars(d, int(cx0 + 30 + j * cw), y + rh // 2 - 8, [min(wd, int(cw) - 30)], 16, bg=(12, 18, 27), a=a)
        else:
            d.ellipse((cx0 + 30, y + rh / 2 - 9, cx0 + 48, y + rh / 2 + 9), outline=SKEL, width=3)
            wd = 300 + (idx * 97) % 600
            bars(d, cx0 + 72, y + 22, [wd], 16, bg=(12, 18, 27), a=a)
            bars(d, cx0 + 72, y + 50, [wd // 2], 11, bg=(12, 18, 27), col=SKEL2, a=a)
        d.line((cx0 + 2, y + rh - 1, cx1 - 2, y + rh - 1), fill=(24, 34, 48))


LAYOUT_FUNCS = {"title": L_title, "cards": L_cards, "checklist": L_checklist, "terminal": L_terminal, "browser": L_browser,
                "ide": L_ide, "flow": L_flow, "stats": L_stats, "feed": L_feed}


# Two layouts side by side - Sat 14 Nov 2026 21:49 CET
def L_split(img, d, S, r):
    x0, y0, x1, y1 = r
    mid, gap = (x0 + x1) // 2, 18
    for side, rect in (("left", (x0, y0, mid - gap, y1)), ("right", (mid + gap, y0, x1, y1))):
        sub = S.spec[side]
        LAYOUT_FUNCS[sub["layout"]](img, d, S.sub(sub, side + "."), rect)


LAYOUT_FUNCS["split"] = L_split


# --- overlays shared by all layouts ----------------------------------------------------------------------------------

# Heading at the top-left with accent underline, fitted font size and two-line wrap - Sat Nov 14 22:31:51 CET 2026
def overlay_heading(d, S):
    h = S.spec.get("heading") if S.spec["layout"] != "browser" else ""
    if h:
        a = prog(S.t, 0.1, 0.5)
        badges = S.spec.get("badges") or []
        max_w = (1720 - max(int(tw(font(28, True), b["text"])) + 56 for b in badges)) if badges else 1760
        sz = fit_size(h, max_w, 50, 34)
        if tw(font(sz, True), h) <= max_w:
            f = font(sz, True)
            T(d, (80, 58 + int((1 - a) * 14)), h, f, fade(TXT, a), "lm")
            d.rectangle((80, 100, 80 + 200 * a, 105), fill=S.acc)
        else:
            f = font(34, True)
            lines = wrapn(h, f, max_w, 2)
            T(d, (80, 44 + int((1 - a) * 14)), lines[0], f, fade(TXT, a), "lm")
            if len(lines) > 1:
                T(d, (80, 84 + int((1 - a) * 14)), lines[1], f, fade(TXT, a), "lm")
            d.rectangle((80, 120, 80 + 200 * a, 125), fill=S.acc)


# Pills along the bottom (callouts), closing line and badges - Sat 14 Nov 2026 21:49 CET
def overlay_bottom(d, S):
    sp, t = S.spec, S.t
    ys = 940
    if sp.get("footer"):
        ys = 892
        a = prog(t, S.times("footer", [sp["footer"]], lo=0.7, hi=1.0)[0], 0.6)
        f = font(fit_size(sp["footer"], 1500, 40, 26), True)
        T(d, (960, 918 + int((1 - a) * 14)), sp["footer"], f, fade(S.acc, a), "mm")
    if sp.get("callouts"):
        cts = S.times("callouts", sp["callouts"], lo=0.25, hi=0.95)
        x = 80
        yy = 836 if sp.get("footer") else 880
        for k, c in enumerate(sp["callouts"]):
            if t >= cts[k]:
                x = pill(d, x, yy, c, S.color("", k + 2), prog(t, cts[k], 0.3), font(24, True), 48) + 16
    badges = sp.get("badges") or []
    if badges:
        bts = S.times("badges", [b["text"] for b in badges], [b.get("cue") for b in badges], lo=0.4, hi=1.0)
        y = 62
        for k, b in enumerate(badges):
            p = prog(t, bts[k], 0.35)
            if p > 0:
                f = font(28, True)
                w = int(tw(f, b["text"])) + 56
                x = W - 80 - w + int((1 - p) * 60)
                col = S.color(b["color"])
                box(d, (x, y, x + w, y + 56), fill=mix(BG, mix(PANEL, col, 0.35), p), outline=fade(col, p), w=3, rad=28)
                T(d, (x + w / 2, y + 28), b["text"], f, fade(WHITE, p), "mm")
            y += 70


# Presenter name plate sliding in at the lower left - Sat 14 Nov 2026 21:49 CET
def overlay_nameplate(d, S):
    n = S.spec.get("nameplate")
    p = prog(S.t, 1.0, 0.6)
    if n and p > 0:
        x, y = 110 + int((1 - p) * -500), 800
        box(d, (x, y, x + 640, y + 120), fill=(10, 16, 26), outline=LINE, w=2, rad=10)
        d.rectangle((x, y, x + 10, y + 120), fill=S.acc)
        T(d, (x + 40, y + 42), n["name"], font(46, True), TXT, "lm")
        if n.get("role"):
            T(d, (x + 40, y + 88), n["role"], font(28), MUTED, "lm")


# Small corner label stating that the screens are illustrations - Sat 14 Nov 2026 21:49 CET
def overlay_label(d, S, text):
    if text:
        f = font(17)
        w = int(tw(f, text)) + 28
        box(d, (W - w - 24, 14, W - 24, 46), fill=(12, 18, 27), outline=LINE, w=1, rad=16)
        T(d, (W - 24 - w / 2, 30), text, f, MUTED, "mm")


# Crop-zoom the frame slowly (push-in) - Sat 14 Nov 2026 21:49 CET
def push_in(img, k):
    if k <= 1.0001:
        return img
    big = img.resize((int(W * k), int(H * k)), Image.Resampling.BILINEAR)
    x, y = (big.width - W) // 2, (big.height - H) // 2
    return big.crop((x, y, x + W, y + H))


# Draw one scene at t seconds into it; returns the image (a new one when a push-in is applied) - Sat Nov 14 22:31:51 CET 2026
def draw_scene(img, i, t, dur, spec, style=None):
    style = style or {}
    S = Ctx(i, spec, t, dur, style.get("accent") or "cyan")
    d = ImageDraw.Draw(img)
    lay = spec["layout"]
    paint_bg(img, d, t, spec.get("background") or "grid")
    top, bottom = 70, 950
    h = spec.get("heading") if lay != "browser" else ""
    badges = spec.get("badges") or []
    if h or badges:
        top = 150
        if h:
            max_w = (1720 - max(int(tw(font(28, True), b["text"])) + 56 for b in badges)) if badges else 1760
            if tw(font(34, True), h) > max_w:
                top = max(top, 180)
    if len(badges) > 1:
        top = max(top, 62 + 70 * len(badges) + 6)
    if spec.get("callouts"):
        bottom -= 70
    if spec.get("footer"):
        bottom -= 60
    overlay_heading(d, S)
    LAYOUT_FUNCS[lay](img, d, S, (80, top, 1840, bottom))
    overlay_bottom(d, S)
    overlay_nameplate(d, S)
    if lay in LABEL_LAYOUTS:
        overlay_label(d, S, spec.get("label", style.get("label", "")))
    if lay == "title":
        img = push_in(img, 1.0 + 0.035 * clamp(t / max(dur, 1.0)))
    return img
