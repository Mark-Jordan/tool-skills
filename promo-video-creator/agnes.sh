#!/usr/bin/env bash
# Agnes API wrapper — ensures Chinese/CJK characters are handled correctly.
# Usage: ./agnes.sh image --prompt "中文提示词" --size 1920x1080 --out output.png
#
# On Windows (Git Bash / MSYS2), Chinese prompts passed via CLI may be garbled.
# Set PYTHONUTF8=1 to force Python to use UTF-8 for all I/O including argv.

export PYTHONUTF8=1
exec python "$(dirname "$0")/scripts/agnes_api.py" "$@"
