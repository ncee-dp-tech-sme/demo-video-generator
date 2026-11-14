#!/usr/bin/env bash
# Thin launcher for install.py (works in Bash and ZSH on macOS and Linux).
# Usage: ./install.sh [--scope workspace|global] [--target DIR] [--demobuilder-dir DIR] [--yes] [--uninstall] [--dry-run]
#
# Change log
# Sat 14 Nov 2026 19:14 CET - Initial version.
# Sat 14 Nov 2026 19:28 CET - Usage line lists --demobuilder-dir.

set -eu

DIR="$(cd "$(dirname "$0")" && pwd)"

PY=""
for cand in python3.14 python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$cand" >/dev/null 2>&1; then
    if "$cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
      PY="$cand"
      break
    fi
  fi
done

if [ -z "$PY" ]; then
  echo "Python 3.10 or newer is required but was not found on PATH." >&2
  exit 1
fi

exec "$PY" "$DIR/install.py" "$@"
