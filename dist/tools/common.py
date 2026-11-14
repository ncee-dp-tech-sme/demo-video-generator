# Shared configuration, structured logging and small helpers for the Demo Narrative Builder tools.
#
# Change log
# Sat 14 Nov 2026 19:14 CET - Initial version: .env loading, JSON logging, slug and word-count helpers.
# Sat 14 Nov 2026 19:14 CET - JsonFormatter so third-party log lines (pypdf) are valid JSON too.
# Sat 14 Nov 2026 19:28 CET - Step 9 settings: DEMOBUILDER_DIR, PIPELINE_PYTHON, VOICE, FPS.
# Sat 14 Nov 2026 21:09 CET - DEMOBUILDER_DIR defaults to the bundled pipeline/ folder when .env does not set it.

import json
import logging
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

HOME = Path(__file__).resolve().parent.parent
load_dotenv(HOME / ".env")  # real environment variables win (override=False)


# Read an integer setting from the environment with a lower bound - Sat 14 Nov 2026 19:14 CET
def _int(name, default, minimum=1):
    try:
        return max(minimum, int(os.environ.get(name, default)))
    except ValueError:
        return default


LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
DEBUG = LOG_LEVEL == "DEBUG"
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "narratives")
TIMEOUT = _int("INGEST_TIMEOUT_SECONDS", 20)
MAX_BYTES = _int("INGEST_MAX_BYTES", 10 * 1024 * 1024, 1024)
MAX_PAGES = _int("INGEST_MAX_PAGES", 300)
MAX_REDIRECTS = _int("INGEST_MAX_REDIRECTS", 5, 0)
USER_AGENT = os.environ.get("INGEST_USER_AGENT", "DemoNarrativeBuilder/1.0")
MIN_WORDS_WARN = _int("MIN_WORDS_WARN", 150, 0)
SPEECH_WPM = _int("SPEECH_WPM", 150, 60)
RUNTIME_TOLERANCE = _int("RUNTIME_TOLERANCE_SECONDS", 10, 0)
PIPELINE_DIR = HOME / "pipeline"                          # bundled pipeline: demo_common.py, build_audio.py, build_video.py, ...
DEMOBUILDER_DIR = os.environ.get("DEMOBUILDER_DIR", "").strip() or str(PIPELINE_DIR)   # empty or unset = bundled pipeline/
PIPELINE_PYTHON = os.environ.get("PIPELINE_PYTHON", "")   # Python with pillow, numpy, imageio-ffmpeg
VOICE = os.environ.get("VOICE", "Daniel")                 # macOS `say` voice
FPS = _int("FPS", 24, 1)

# Timing constants shared with the Demobuilder video pipeline (demo_common.py).
BEAT_GAP = 0.65
LEAD_IN = 0.35
TAIL = 0.25

# Formats every log record as one JSON object; JSON messages from event() are embedded as fields - Sat 14 Nov 2026 19:14 CET
class JsonFormatter(logging.Formatter):
    def format(self, record):
        msg = record.getMessage()
        try:
            data = json.loads(msg)
            fields = data if isinstance(data, dict) else {"msg": msg}
        except ValueError:
            fields = {"msg": msg}
        out = {"time": self.formatTime(record), "level": record.levelname, **fields}
        if record.exc_info:
            out["exc"] = self.formatException(record.exc_info)
        return json.dumps(out, ensure_ascii=True)


_handler = logging.StreamHandler(sys.stderr)
_handler.setFormatter(JsonFormatter())
logging.basicConfig(
    level=getattr(logging, "WARNING" if LOG_LEVEL == "WARN" else LOG_LEVEL, logging.INFO),
    handlers=[_handler],
)
log = logging.getLogger("dnb")


# Log one structured event; values are JSON-encoded so they cannot break the log format - Sat 14 Nov 2026 19:14 CET
def event(level, name, **fields):
    log.log(level, json.dumps({"event": name, **fields}, ensure_ascii=True))


# Turn free text into a safe folder/file slug (letters, digits, dashes) - Sat 14 Nov 2026 19:14 CET
def slugify(text, fallback="narrative", limit=60):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:limit].strip("-")
    return s or fallback


# Count words the way the voice-over timing check does - Sat 14 Nov 2026 19:14 CET
def word_count(text):
    return len(re.findall(r"\b[\w'’-]+\b", text))
