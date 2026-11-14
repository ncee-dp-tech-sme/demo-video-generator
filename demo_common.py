# Shared config, script parsing and timeline helpers for the demo video builders (HexStrike + IBM Bob).
#
# Change log
# Sat 14 Nov 2026 17:25 CET - Initial version: script parser, TTS text fixes, timeline + cue helpers.
# Sat 14 Nov 2026 17:58 CET - SCRIPT_FILE / BUILD_DIR env overrides (defaults unchanged); Bob TTS fixes.

import json
import logging
import os
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent
SCRIPT_MD = ROOT / os.environ.get("SCRIPT_FILE", "HexStrike_AV_script_v1.md")
BUILD = ROOT / os.environ.get("BUILD_DIR", "build")
OUT = ROOT / "output"
TIMELINE_JSON = BUILD / "timeline.json"

VOICE = os.environ.get("VOICE", "Daniel")
SPEECH_RATE = int(os.environ.get("SPEECH_RATE", "185"))
FPS = int(os.environ.get("FPS", "24"))
W, H = 1920, 1080
BEAT_GAP = 0.65      # seconds of silence for a [BEAT]
LEAD_IN = 0.35       # seconds before VO starts in each scene
TAIL = 0.25          # seconds of silence kept at end of each scene

logging.basicConfig(
    level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
)
log = logging.getLogger("demo")

# Pronunciation fixes applied to text sent to the TTS engine only (captions keep the original).
TTS_FIXES = [
    (r"\bNmap\b", "En map"), (r"\bMasscan\b", "Mass scan"), (r"\bNuclei\b", "New clee eye"),
    (r"\bNikto\b", "Nick toe"), (r"\bGobuster\b", "Go buster"), (r"\bFFUF\b", "eff eff you eff"),
    (r"\bSQLMap\b", "sequel map"), (r"\bSQLite\b", "sequel lite"), (r"\bTrivy\b", "Trivvy"),
    (r"\bOWASP\b", "oh wasp"), (r"\bCVSS\b", "C V S S"), (r"\bCWE\b", "C W E"),
    (r"\bCVE\b", "C V E"), (r"\bPDF\b", "P D F"), (r"\bAPI\b", "A P I"), (r"\bMCP\b", "M C P"),
    (r"1min\.AI", "one min A I"), (r"OpenAI", "Open A I"), (r"\brun\.sh\b", "run dot S H"),
    (r"127\.0\.0\.1", "one twenty seven dot zero dot zero dot one"), (r"\bBurp\b", "Burp"),
    (r"\bPodman\b", "Pod man"), (r"\bv3\.1\b", "version three point one"),
    (r"\bPython 3\.10\b", "Python three ten"), (r"\bDevSecOps\b", "Dev Sec Ops"),
    (r"\bPentestGuard\b", "Pentest Guard"), (r"\bHexStrike\b", "Hex Strike"), (r"\s+—\s+", ", "),
    # IBM Bob demo
    (r"\bGitHub\b", "Git Hub"), (r"\bREADME\b", "read me"), (r"\bIDE\b", "I D E"),
    (r"\bUI\b", "U I"), (r"\bPR\b", "P R"),
]

SCENES = []     # filled by load_scenes()
TL = []         # filled by set_timeline()


# Parse the markdown script table into scene dicts (start, end, visual, vo) - Sat 14 Nov 2026 17:25 CET
def load_scenes():
    rows = []
    pat = re.compile(r"^\|\s*(\d+):(\d+)\s*[–-]\s*(\d+):(\d+)\s*\|(.*?)\|(.*)\|\s*$")
    for line in SCRIPT_MD.read_text(encoding="utf-8").splitlines():
        m = pat.match(line)
        if m:
            a, b, c, d = (int(x) for x in m.groups()[:4])
            rows.append({"start": a * 60 + b, "end": c * 60 + d,
                         "visual": m.group(5).strip(), "vo": m.group(6).strip()})
    SCENES[:] = rows
    return rows


# Split a VO string into parts at [BEAT] markers - Sat 14 Nov 2026 17:25 CET
def split_parts(vo):
    return [p.strip() for p in re.split(r"\s*\[BEAT\]\s*", vo) if p.strip()]


# Apply pronunciation fixes for the TTS engine - Sat 14 Nov 2026 17:25 CET
def tts_text(s):
    for pat, rep in TTS_FIXES:
        s = re.sub(pat, rep, s)
    return s


# Store the timeline and derive caption segments - Sat 14 Nov 2026 17:25 CET
def set_timeline(tl):
    TL[:] = tl
    return TL


# Load the timeline written by the audio stage - Sat 14 Nov 2026 17:25 CET
def load_timeline():
    load_scenes()
    set_timeline(json.loads(TIMELINE_JSON.read_text()))
    return TL


# Time (seconds, relative to scene start) at which a phrase is spoken - Sat 14 Nov 2026 17:25 CET
def cue(scene, phrase, lead=0.1):
    p = phrase.lower()
    for part in TL[scene]["parts"]:
        idx = part["text"].lower().find(p)
        if idx >= 0:
            return max(0.0, part["t0"] + part["dur"] * idx / max(1, len(part["text"])) - lead)
    raise KeyError(f"cue phrase not found in scene {scene}: {phrase}")


# Caption segments (absolute start, end, text), split per sentence - Sat 14 Nov 2026 17:25 CET
def captions():
    segs = []
    for sc in TL:
        for part in sc["parts"]:
            sents = [s for s in re.split(r"(?<=[.!?])\s+", part["text"]) if s]
            total = sum(len(s) for s in sents) or 1
            t = sc["start"] + part["t0"]
            for s in sents:
                dur = part["dur"] * len(s) / total
                segs.append((t, t + dur, s))
                t += dur
    return segs
