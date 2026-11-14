# Storyboard for step 9 (video production): turns every row of an approved script table into a scene spec that
# scene_engine.py renders as animated mock screens (terminal, browser, IDE with assistant panel, cards, checklist,
# architecture flow, stats, feeds). Two sources: (1) the automatic planner below, which reads the VISUAL and VO
# cells, and (2) a storyboard.json that the mode (or a person) refines per scene. Pure Python, no imaging imports.
#
# Usage: python storyboard.py <script.md> [--write storyboard.json] [--force]
#
# Change log
# Sat 14 Nov 2026 21:49 CET - Initial version: VISUAL/VO planner, schema normalisation, merge with storyboard.json.

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

LAYOUTS = ("title", "cards", "checklist", "terminal", "browser", "ide", "flow", "stats", "feed", "split")
COLORS = ("cyan", "blue", "green", "amber", "purple", "red")
ROW = re.compile(r"^\|\s*(\d+):(\d+)\s*[–-]\s*(\d+):(\d+)\s*\|(.*?)\|(.*)\|\s*$")
SPAN = re.compile(r"`([^`]+)`")
COMMANDS = set("""git gh ls cd cat echo mkdir rm cp mv touch python python3 pip pip3 npm npx yarn node docker podman
kubectl oc helm terraform ansible curl wget make bash sh zsh nmap sudo ssh scp tar chmod export source java mvn
gradle go cargo brew apt ibmcloud bob uv pytest""".split())
KEYWORDS = {
    "ide": r"\bide\b|editor|diff\b|file tree|explorer|assistant panel|bob panel|vs ?code|source code|code view",
    "terminal": r"terminal|shell|command line|\bcli\b|console|boot sequence|run\.sh",
    "browser": r"browser|web ?page|website|dashboard|\burl\b|https?://|modal|banner|web ui|form fields?|github-style",
    "flow": r"diagram|architecture|connects? to|pipeline|flowchart|\bnodes?\b|boxes",
    "checklist": r"checklist|check list|ticks?\b|builds? line by line|ticking",
    "cards": r"\bcards?\b|pillars?|columns?|options?|tiles?|use-case",
    "stats": r"counter|metric|\bkpi\b|big number|overlay",
    "feed": r"scroll|backlog|issues? list|table|ledger|\brows?\b|feed|timeline",
    "title": r"title card|end card|logo|name-?plate|plain background|fade to black|hard cut to black",
}
LIMITS = {"cards": 8, "items": 10, "lines": 24, "nodes": 6, "stats": 4, "files": 16, "code": 14, "rows": 8}
NOISE = re.compile(r"stylised|illustration|corner label|made with ibm bob", re.I)


# Table rows of a script: start, end (seconds), visual cell, vo cell - Sat 14 Nov 2026 21:49 CET
def parse_rows(text):
    rows = []
    for line in text.splitlines():
        m = ROW.match(line)
        if m:
            a, b, c, d = (int(x) for x in m.groups()[:4])
            rows.append({"start": a * 60 + b, "end": c * 60 + d, "visual": m.group(5).strip(), "vo": m.group(6).strip()})
    return rows


# sha256 of a script text, to tell which script a storyboard was made for - Sat 14 Nov 2026 21:49 CET
def script_sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# Collapse whitespace and cut at a word boundary - Sat 14 Nov 2026 21:49 CET
def short(s, n=140):
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    if len(s) <= n:
        return s
    cut = s[: n - 3].rsplit(" ", 1)[0] if " " in s[: n - 3] else s[: n - 3]
    return cut.rstrip(" ,;:-") + "..."


# Remove markdown emphasis and backticks - Sat 14 Nov 2026 21:49 CET
def plain(s):
    return re.sub(r"\s+", " ", re.sub(r"[*`]+", "", s or "")).strip()


# Split a VISUAL cell into SCENE / ON-SCREEN / DEMO / TRANSITION (markdown kept); unlabelled cells become SCENE - Sat 14 Nov 2026 21:49 CET
def parse_visual(cell):
    out, last = {}, None
    for chunk in re.split(r"<br\s*/?>", cell):
        m = re.match(r"\s*\**\s*(SCENE|ON-SCREEN|DEMO|TRANSITION)\b[^:]{0,80}:\s*\**\s*(.*)", chunk, re.I | re.S)
        if m:
            last = m.group(1).upper()
            out[last] = out.get(last, "") + (" " if last in out else "") + m.group(2).strip()
        elif last and chunk.strip():
            out[last] += " " + chunk.strip()
    if not out:
        out["SCENE"] = re.sub(r"<br\s*/?>", " ", cell).strip()
    return out


# Backtick spans of a text, in order - Sat 14 Nov 2026 21:49 CET
def spans(s):
    return [x.strip() for x in SPAN.findall(s or "") if x.strip()]


# Does a string look like a shell command? - Sat 14 Nov 2026 21:49 CET
def is_command(s):
    t = s.strip()
    t = t[2:] if t.startswith("$ ") else t
    first = t.split()[0] if t.split() else ""
    return first in COMMANDS or first.startswith(("./", "~/"))


# Does a string look like a file or folder name? - Sat 14 Nov 2026 21:49 CET
def is_file(s):
    return bool(re.fullmatch(r"[\w./<>-]*\.[A-Za-z0-9]{1,5}/?|[\w.-]+/", s.strip())) and not is_command(s)


# Does a string look like a URL or host:port? - Sat 14 Nov 2026 21:49 CET
def is_url(s):
    return bool(re.search(r"https?://|localhost|\d+\.\d+\.\d+\.\d+(:\d+)?", s)) and " " not in s.strip()


# A sentence-like line (a closing message), as opposed to a label - Sat 14 Nov 2026 21:49 CET
def sentence_like(s):
    return bool(re.search(r"[a-z]", s)) and s.rstrip().endswith((".", "!", "?")) and len(s.split()) >= 3


# Labels from ON-SCREEN spans: split "A · B | C" and drop commands, files, URLs and disclaimer labels - Sat 14 Nov 2026 21:49 CET
def labels_of(sp):
    out = []
    for s in sp:
        if is_command(s) or is_file(s) or is_url(s) or NOISE.search(s):
            continue
        out += [x.strip() for x in re.split(r"\s+[·|]\s+", s) if x.strip()]
    return out


# Leading number of a text -> (value, label); "1 in 5 customers" -> ("1 in 5", "customers") - Sat 14 Nov 2026 21:49 CET
def split_number(s):
    m = re.match(r"^(\d[\d,.]*\s*(?:in|of|out of|/)\s*\d[\d,.]*%?|\d[\d,.]*\s*[%+xkKmM]?)(?:\s+(.*))?$", s.strip())
    return (m.group(1).strip(), (m.group(2) or "").strip(" .")) if m else ("", s.strip(" ."))


# Up to n short key phrases from the voice-over, used when the VISUAL cell names nothing to show - Sat 14 Nov 2026 21:49 CET
def key_points(vo, n=4):
    text = re.sub(r"\[BEAT\]", " ", vo)
    out = []
    for sent in re.split(r"(?<=[.!?])\s+", text):
        words = sent.strip(" .!?").split()
        if len(words) >= 3:
            out.append(short(" ".join(words), 60))
    return out[:n]


# First comma list after a colon or dash inside one sentence: "- Nmap, Nuclei, Gobuster" -> items - Sat 14 Nov 2026 21:49 CET
def list_after(text):
    word = r"[A-Za-z][\w+.-]*(?: [A-Za-z][\w+.-]*){0,2}"
    for sent in re.split(r"(?<=[.!?])\s+", text):
        m = re.search(rf"[:—–-]\s*({word}(?:,\s*(?:and\s+)?{word}){{2,}})", sent)
        if m:
            return [x.strip(" .") for x in re.split(r",\s*(?:and\s+)?", m.group(1)) if x.strip(" .")]
    return []


# Count of keyword matches per layout family - Sat 14 Nov 2026 21:49 CET
def keyword_hits(low):
    return {k: len(re.findall(rx, low)) for k, rx in KEYWORDS.items()}


# Plan one scene from its VISUAL and VO cells; returns an un-normalised spec - Sat 14 Nov 2026 21:49 CET
def plan_scene(cell, vo, idx=0, count=1):
    p = parse_visual(cell)
    onscr, demo = p.get("ON-SCREEN", ""), p.get("DEMO", "")
    full = " ".join(v for k, v in p.items() if k != "TRANSITION")
    flat = plain(full).replace("“", '"').replace("”", '"')
    low = flat.lower()
    on_sp, demo_sp, all_sp = spans(onscr), spans(demo), spans(full)
    hits = keyword_hits(plain(p.get("SCENE", "") + " " + p.get("DEMO", "")).lower())   # how the scene looks, not what it says
    cmds = list(dict.fromkeys(s for s in all_sp if is_command(s)))
    files = list(dict.fromkeys(s for s in demo_sp if is_file(s)))
    urls = list(dict.fromkeys(s for s in all_sp if is_url(s))) or re.findall(r"https?://\S+|\b\d+\.\d+\.\d+\.\d+:\d+\b", flat)
    quotes = re.findall(r'"([^"]{3,100})"', flat)
    labels = labels_of(on_sp) or labels_of(all_sp)
    lst = list_after(flat)
    feed_cols = next((list_after(s) for s in re.split(r"(?<=[.!?])\s+", flat) if re.search(r"table|ledger|rows?|columns?|log\b", s, re.I)), [])
    pairs = [(a.strip(), short(b.strip(" ."), 110)) for a, b in re.findall(
        r"`([^`]{2,50})`\s*:\s*(.+?)(?=\s*(?:Card\s*\w+\s*)?`[^`]{2,50}`\s*:|$)", onscr, re.S)]
    spec = {}

    # overlays shared by every layout: callouts, badges, name plate, closing line, background
    callouts = []
    for m in re.finditer(r"[Cc]allout[^`]*((?:`[^`]+`(?:\s*[·,]\s*)?)+)", full):
        callouts += spans(m.group(1))
    if callouts:
        spec["callouts"] = [short(c, 70) for c in callouts][:4]
    badges = []
    for m in re.finditer(r"(green|red|amber)?\s*`([^`]+)`\s*(?:badge|label)\b|badge\s*`([^`]+)`", full, re.I):
        text = m.group(2) or m.group(3)
        if not NOISE.search(text):
            badges.append({"text": short(text, 40), "color": {"red": "red", "amber": "amber"}.get((m.group(1) or "green").lower(), "green")})
    if badges:
        spec["badges"] = badges[:3]
    lt = re.search(r"[Ll]ower-third:\s*`([^`]+)`", full)
    if lt:
        name, _, role = lt.group(1).partition(",")
        spec["nameplate"] = {"name": short(name, 30), "role": short(role.strip(), 40)}
    foot = [s for s in labels if sentence_like(s)]
    if foot:
        spec["footer"] = short(foot[-1], 90)
    taken = set(foot) | set(callouts) | {b["text"] for b in badges}
    labels = [s for s in labels if s not in taken and not (lt and s in lt.group(1))]
    if re.search(r"scroll|backlog", low):
        spec["background"] = "feed"

    prompt = ""
    m = re.search(r'\*"([^*]{8,260})"\*|\*([^*"]{12,260})\*', demo)
    if m:
        prompt = plain(m.group(1) or m.group(2))
    elif "DEMO" in p and quotes and len(quotes[0].split()) >= 3:
        prompt = quotes[0]
    mode = re.search(r"\b(Plan|Agent|Ask|Code)\s+mode\b", flat, re.I)

    def keep(layout, **kw):
        spec["layout"] = layout
        spec.update({k: v for k, v in kw.items() if v})
        return spec

    # browser content: URL, modal from a quoted "Title: text", badge from a quoted CAPS text, rows from labels
    def browser_spec(rows_from_labels=False):
        b = {"layout": "browser", "url": urls[0] if urls else ""}
        modal = next((q for q in quotes if " — " in q or ": " in q), "") if re.search(r"modal|dialog|pop-?up|banner", low) else ""
        if modal:
            mt, _, mx = modal.replace(" — ", "|").replace(": ", "|").partition("|")
            b["modal"] = {"title": short(mt, 50), "text": short(mx.strip(), 80), "color": "red"}
        head = next((q for q in quotes if len(q) <= 24 and not q.isupper() and ": " not in q and " — " not in q), "")
        if head:
            b["heading"] = head
        caps = next((q for q in quotes if q.isupper() and len(q) < 28), "")
        if caps and not spec.get("badges"):
            spec["badges"] = [{"text": caps, "color": "red"}]
        if rows_from_labels and len(labels) >= 2:
            b["rows"] = [{"text": short(s, 60), "chip": "OK", "color": "green"} for s in labels[:LIMITS["rows"]]]
        return b

    # progress-strip title card ("PART 1: BUILD")
    part = next((s for s in labels if re.match(r"^[A-Z][A-Z0-9 ]{1,14}:\s*\S+", s)), None)
    if part:
        k, _, t = part.partition(":")
        steps = [s for s in labels if re.fullmatch(r"[A-Z]{3,12}", s)]
        active = max([i for i, s in enumerate(steps) if re.search(rf"`{s}`\s+lit", full)] or [0])
        sub = next((s for s in labels if s != part and s not in steps), "")
        return keep("title", kicker=k.strip(), title=t.strip(), subtitle=short(sub, 90), steps=steps, active=active)

    # explicit "label: description" pairs -> cards
    if len(pairs) >= 2 and not cmds:
        return keep("cards", cards=[{"title": short(a, 36), "text": b} for a, b in pairs][:LIMITS["cards"]])

    # commands: IDE with terminal pane, terminal beside a browser, or a plain terminal
    outs = [s for s in demo_sp if not is_command(s) and not is_file(s) and not is_url(s) and re.search(r"\d", s)
            and re.search(r"passed|failed|error|changed|created|installed|merged|listening|running|\bok\b|\bdone\b", s, re.I)
            and len(s.split()) <= 6 and not re.search(r"[(=]", s)]
    cmd_lines = [("$ " + c.lstrip("$ ").strip()) for c in cmds]
    pillars = len(labels) >= 2 and bool(re.search(KEYWORDS["cards"], low)) and not cmds
    ide_like = (hits["ide"] or len(files) >= 3) and not pillars
    if ide_like:
        plan = [s for s in demo_sp if re.search(r"\bplan\b", low) and not is_command(s) and not is_file(s) and not is_url(s)
                and len(s.split()) <= 3 and "." not in s and not re.search(r"\d", s)][:8]
        panel = {"title": "Assistant", "mode": (mode.group(1).upper() if mode else ""),
                 "messages": [prompt] if prompt else [], "plan": plan}
        code = [s for s in demo_sp if re.search(r"[(=]", s) and not is_command(s)][:LIMITS["code"]]
        return keep("ide", files=files[:LIMITS["files"]], editor={"file": files[0] if files else "", "code": code},
                    panel=panel if (panel["messages"] or panel["plan"]) else {}, terminal=(cmd_lines + outs)[:8])
    if cmds:
        lines = (cmd_lines + outs)[:LIMITS["lines"]]
        if hits["browser"] or urls:
            return {**spec, "layout": "split", "left": {"layout": "terminal", "lines": lines, "window_title": "Terminal"},
                    "right": browser_spec(rows_from_labels=True)}
        return keep("terminal", lines=lines, window_title="Terminal")

    # architecture / flow
    if hits["flow"] and (len(quotes) >= 2 or len(labels) >= 2):
        names = list(quotes)
        node = re.search(r"\b([A-Z][\w-]*) node\b", flat)
        if node and node.group(1) not in names:
            names.insert(0, node.group(1))
        nodes = []
        for nm in (names or labels)[:LIMITS["nodes"]]:
            a, _, b = nm.partition(" — ")
            nodes.append({"label": short(a, 32), "sub": short(b, 40)})
        return keep("flow", nodes=nodes)

    # browser-like screen
    if hits["browser"] and (urls or quotes or hits["browser"] >= 2):
        return keep(**browser_spec(rows_from_labels=bool(hits["checklist"])))

    # numbers
    nums = [s for s in (labels or quotes) if re.search(r"\d", s)]
    parts = []
    for s in nums:
        halves = [x.strip() for x in s.split(" / ")]
        parts += halves if len(halves) > 1 and all(re.match(r"\d", x) for x in halves) else [s]
    if 1 <= len(parts) <= 4 and not hits["checklist"] and (hits["stats"] or len(parts) == len(labels or quotes)):
        stats = []
        for s in parts:
            v, lab = split_number(s)
            stats.append({"value": v or short(s, 14), "label": short(lab, 40)})
        return keep("stats", stats=stats)

    # list-like screens, title cards, cards and checklists
    items = labels or (lst if not on_sp else [])
    if hits["title"] and len(items) <= 1:
        head = items[0] if items else (key_points(vo, 1) or [short(flat, 60)])[0]
        return keep("title", title=short(head, 70))
    if hits["feed"] and (feed_cols or not labels):
        return keep("feed", columns=feed_cols[:5], title=short(flat.split(".")[0], 60))
    if not items and idx in (0, count - 1):
        head = items[0] if items else (key_points(vo, 1) or [short(flat, 60)])[0]
        return keep("title", title=short(head, 70))
    items = items or key_points(vo)
    if hits["checklist"]:
        return keep("checklist", items=[{"text": short(i, 70)} for i in items][:LIMITS["items"]])
    if len(items) == 1:
        return keep("title", title=short(items[0], 70))
    return keep("cards", cards=[{"title": short(i, 36)} for i in items][:LIMITS["cards"]])


# --- schema ---------------------------------------------------------------------------------------------------------

# Clean text value - Sat 14 Nov 2026 21:49 CET
def _txt(v, n=140):
    return short(plain(str(v)) if v is not None and not isinstance(v, (dict, list)) else "", n)


# Colour name or default - Sat 14 Nov 2026 21:49 CET
def _col(v, default=""):
    v = str(v or "").lower()
    return v if v in COLORS else default


# Items as dicts with a text key (strings allowed) - Sat 14 Nov 2026 21:49 CET
def _items(v, limit, keys, n=140):
    out = []
    for x in v if isinstance(v, list) else []:
        d = x if isinstance(x, dict) else {keys[0]: x}
        row = {k: (_col(d.get(k)) if k == "color" else _txt(d.get(k), n)) for k in keys}
        if k_has(row, keys[0]):
            if isinstance(d.get("cue"), str) and d["cue"].strip():
                row["cue"] = _txt(d["cue"], 60)
            out.append(row)
    return out[:limit]


# Row has a non-empty primary value - Sat 14 Nov 2026 21:49 CET
def k_has(row, key):
    return bool(row.get(key))


# String list - Sat 14 Nov 2026 21:49 CET
def _strs(v, limit, n=140):
    return [t for t in (_txt(x, n) for x in (v if isinstance(v, list) else [])) if t][:limit]


# Normalise one scene spec; returns (clean spec or None, problems) - Sat 14 Nov 2026 21:49 CET
def normalize_scene(sc, depth=0):
    if not isinstance(sc, dict):
        return None, ["scene is not an object"]
    lay = str(sc.get("layout", "")).lower()
    if lay not in LAYOUTS:
        return None, [f"unknown layout {lay!r} (use one of {', '.join(LAYOUTS)})"]
    out, problems = {"layout": lay}, []
    for k, n in (("heading", 70), ("footer", 100), ("label", 60), ("kicker", 40), ("title", 80), ("subtitle", 110),
                 ("window_title", 40), ("url", 70), ("button", 30), ("cue", 60)):
        if sc.get(k):
            out[k] = _txt(sc[k], n)
    if str(sc.get("background", "")).lower() in ("feed", "grid", "none"):
        out["background"] = str(sc["background"]).lower()
    if _col(sc.get("color")):
        out["color"] = _col(sc["color"])
    if sc.get("callouts"):
        out["callouts"] = _strs(sc["callouts"], 4, 70)
    raw = (sc.get("badges") if isinstance(sc.get("badges"), list) else []) + ([sc["badge"]] if isinstance(sc.get("badge"), dict) else [])
    badges = []
    for b in raw:
        if isinstance(b, dict) and b.get("text"):
            badges.append({"text": _txt(b["text"], 40), "color": _col(b.get("color"), "green")})
            if b.get("cue"):
                badges[-1]["cue"] = _txt(b["cue"], 60)
    if badges:
        out["badges"] = badges[:3]
    if isinstance(sc.get("nameplate"), dict) and sc["nameplate"].get("name"):
        out["nameplate"] = {"name": _txt(sc["nameplate"]["name"], 30), "role": _txt(sc["nameplate"].get("role"), 40)}
    if lay == "title":
        out["steps"] = _strs(sc.get("steps"), 5, 20)
        out["active"] = int(sc["active"]) if str(sc.get("active", "")).isdigit() else 0
        if sc.get("feed"):
            out["background"] = "feed"
        if not (out.get("title") or out.get("kicker")):
            problems.append("title layout needs a title")
    elif lay == "cards":
        out["cards"] = _items(sc.get("cards"), LIMITS["cards"], ("title", "text", "color"), 120)
        if not out["cards"]:
            problems.append("cards layout needs a non-empty cards list")
    elif lay == "checklist":
        out["items"] = _items(sc.get("items"), LIMITS["items"], ("text",), 90)
        if not out["items"]:
            problems.append("checklist layout needs a non-empty items list")
    elif lay == "terminal":
        out["lines"] = _strs(sc.get("lines"), LIMITS["lines"], 110)
        if not out["lines"]:
            problems.append("terminal layout needs a non-empty lines list")
    elif lay == "browser":
        out["nav"] = _strs(sc.get("nav"), 6, 24)
        out["rows"] = _items(sc.get("rows"), LIMITS["rows"], ("text", "chip", "color"), 80)
        for k in ("modal",):
            if isinstance(sc.get(k), dict) and (sc[k].get("title") or sc[k].get("text")):
                m = sc[k]
                out[k] = {"title": _txt(m.get("title"), 50), "text": _txt(m.get("text"), 100),
                          "button": _txt(m.get("button"), 24), "color": _col(m.get("color"), "red")}
    elif lay == "ide":
        out["files"] = _strs(sc.get("files"), LIMITS["files"], 40)
        ed = sc.get("editor") if isinstance(sc.get("editor"), dict) else {}
        out["editor"] = {"file": _txt(ed.get("file"), 40), "code": _strs(ed.get("code"), LIMITS["code"], 100)}
        pn = sc.get("panel") if isinstance(sc.get("panel"), dict) else {}
        if pn:
            out["panel"] = {"title": _txt(pn.get("title"), 24), "mode": _txt(pn.get("mode"), 12).upper(),
                            "messages": _strs(pn.get("messages"), 5, 260), "plan": _strs(pn.get("plan"), 8, 60)}
        out["terminal"] = _strs(sc.get("terminal"), 8, 110)
        if not (out["files"] or out["editor"]["code"] or out.get("panel") or out["terminal"]):
            problems.append("ide layout needs files, editor code, a panel or terminal lines")
    elif lay == "flow":
        out["nodes"] = _items(sc.get("nodes"), LIMITS["nodes"], ("label", "sub", "color"), 50)
        out["chips"] = _strs(sc.get("chips"), 4, 40)
        if len(out["nodes"]) < 2:
            problems.append("flow layout needs at least two nodes")
    elif lay == "stats":
        out["stats"] = _items(sc.get("stats"), LIMITS["stats"], ("value", "label", "color"), 50)
        if not out["stats"]:
            problems.append("stats layout needs a non-empty stats list")
    elif lay == "feed":
        out["items"] = _items(sc.get("items"), 12, ("text", "chip", "color"), 80)
        out["columns"] = _strs(sc.get("columns"), 5, 24)
        if str(sc.get("highlight", "")).isdigit():
            out["highlight"] = int(sc["highlight"])
    elif lay == "split" and depth == 0:
        for side in ("left", "right"):
            sub, pr = normalize_scene(sc.get(side), depth + 1)
            if sub is None or sub["layout"] == "split":
                problems.append(f"split.{side}: {pr[0] if pr else 'nested split is not allowed'}")
            else:
                out[side] = sub
                problems += [f"split.{side}: {x}" for x in pr]
    elif lay == "split":
        return None, ["split cannot be nested"]
    return out, problems


# Automatic storyboard for a script text - Sat 14 Nov 2026 21:49 CET
def auto_storyboard(script_text):
    rows = parse_rows(script_text)
    scenes = []
    for i, r in enumerate(rows):
        spec, pr = normalize_scene(plan_scene(r["visual"], r["vo"], i, len(rows)))
        scenes.append(spec if spec and not pr else {"layout": "title", "title": short(plain(r["visual"]), 60) or "Scene"})
    return {"version": 1, "source": "auto", "script_sha256": script_sha(script_text),
            "style": {"label": "Illustrative mock-up, not product footage"}, "scenes": scenes}


# Merge a user storyboard over the automatic one; invalid or missing scenes fall back to the automatic scene - Sat 14 Nov 2026 21:49 CET
def merge(script_text, user=None):
    auto = auto_storyboard(script_text)
    problems = []
    if not isinstance(user, dict):
        return auto, problems
    ulist = user.get("scenes") if isinstance(user.get("scenes"), list) else []
    if len(ulist) != len(auto["scenes"]):
        problems.append(f"storyboard has {len(ulist)} scenes, the script has {len(auto['scenes'])}; missing scenes use the automatic plan")
    if user.get("script_sha256") and user.get("script_sha256") != auto["script_sha256"]:
        problems.append("storyboard was made for another version of the script (check that the scenes still match)")
    scenes, used = [], 0
    for i, a in enumerate(auto["scenes"]):
        spec, pr = normalize_scene(ulist[i]) if i < len(ulist) and ulist[i] else (None, [])
        problems += [f"scene {i + 1}: {x}" for x in pr]
        scenes.append(spec if spec and not pr else a)
    style = user.get("style") if isinstance(user.get("style"), dict) else auto["style"]
    return {"version": 1, "source": "storyboard.json", "script_sha256": auto["script_sha256"],
            "style": {"label": _txt(style.get("label", ""), 60), "accent": _col(style.get("accent"), "cyan")},
            "scenes": scenes}, problems


# Load storyboard.json (if present) and merge it with the automatic plan - Sat 14 Nov 2026 21:49 CET
def load(script_path, storyboard_path=None):
    script_path = Path(script_path)
    text = script_path.read_text(encoding="utf-8")
    sp = Path(storyboard_path) if storyboard_path else script_path.parent / "storyboard.json"
    user = None
    if sp.is_file():
        try:
            user = json.loads(sp.read_text(encoding="utf-8"))
        except ValueError:
            sb, problems = merge(text, None)
            return sb, [f"{sp.name} is not valid JSON; the automatic plan is used"]
    return merge(text, user)


# Command-line entry point: print or write the automatic storyboard - Sat 14 Nov 2026 21:49 CET
def main(argv=None):
    ap = argparse.ArgumentParser(description="Automatic storyboard from a script table")
    ap.add_argument("script")
    ap.add_argument("--write", help="write the storyboard JSON to this file (refuses to overwrite without --force)")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    sb, problems = load(a.script, a.write or None) if not a.write else (auto_storyboard(Path(a.script).read_text(encoding="utf-8")), [])
    if a.write:
        out = Path(a.write)
        if out.exists() and not a.force:
            print(f"{out} exists; pass --force to overwrite", file=sys.stderr)
            return 1
        out.write_text(json.dumps(sb, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for i, sc in enumerate(sb["scenes"], 1):
        print(f"scene {i}: {sc['layout']}")
    for p in problems:
        print("warning:", p, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
